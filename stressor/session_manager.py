# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re
import time
from copy import deepcopy

import requests

from snazzy import red, yellow
from stressor.config_manager import replace_var_macros
from stressor.context_stack import ContextStack
from stressor.plugins.base import ActivityAssertionError
from stressor.util import (
    NO_DEFAULT,
    StressorError,
    check_arg,
    get_dict_attr,
    logger,
    shorten_string,
)


class StoppedError(StressorError):
    """Raised when an activity stops due because the `stop_request` is set."""


class SkippedError(StressorError):
    """Raised when an activity is skipped due to `max_errors` or `max_time`."""


class User:
    def __init__(self, name, password, **kwargs):
        self.name = name
        self.password = password
        for arg_name, arg_val in kwargs.items():
            assert type(arg_name) in (int, float, str)
            setattr(self, arg_name, arg_val)
        return

    def __str__(self):
        return "User<{}>".format(self.name)

    @property
    def auth(self):
        """Return (name, password) tuple or None."""
        if self.password is None:
            return None
        return (self.name, self.password)


class SessionHelper:
    """Passed to script activities."""

    def __init__(self, session):
        self.__session = session

    @property
    def browser(self):
        return self.__session.browser_session


class SessionManager:
    """
    Run a scenario in a single session.
    """

    #: (float)
    DEFAULT_TIMEOUT = 10.0

    def __init__(self, run_manager, context, session_id, user):
        # check_arg(run_manager, RunManager)
        check_arg(context, dict)
        check_arg(session_id, str)
        check_arg(user, User, or_none=True)

        #: The :class:`RunManager` object that holds global settings and definitions
        self.run_manager = run_manager
        config = run_manager.config_manager.config

        # (dict) Global variables for this session. Initialized from the
        # run configuration, but not shared between sessions.
        # (`self.context` is accessible by the respective property below.)
        context = context.copy()
        #: (str) Unique ID string for this session
        self.session_id = session_id
        #: The :class:`User` object that is assigned to this session
        self.user = user or User("anonymous", "")
        #: (dict) Copy of `run_config.sessions` configuration
        self.sessions = run_manager.config_manager.sessions.copy()
        #: (bool) True: only simulate activities
        self.dry_run = bool(context.get("dry_run"))
        #: (int) Verbosity 0..5
        self.verbose = context.get("verbose", 3)
        #: (:class:`threading.Event`)
        self.stop_request = run_manager.stop_request

        # Set some default entries in context dict
        context.setdefault("timeout", self.DEFAULT_TIMEOUT)
        context.setdefault("session_id", self.session_id)
        context.setdefault("user", self.user)

        #: The :class:`~stressor.context_stack.ContextStack` object that reflects the current execution path
        self.context_stack = ContextStack(run_manager.host_id, context)
        self.context_stack.push(run_manager.process_id)
        self.context_stack.push(session_id)
        #: :class:`~stressor.statistic_manager.StatisticManager` object that containscurrent execution path
        self.stats = run_manager.stats
        # Lazy initialization using a property
        self._browser_session = None

        #: (int) Stop session if global error count > X
        #: Passing `--max-errors` will override this.
        self.max_errors = int(config.get("max_errors", 0))

        #: (float) Stop session if total run time  > X seconds.
        #: Passing `--max-time` will override this.
        self.max_time = float(config.get("max_time", 0.0))
        self._cancelled_seq = None

        # Used by StatisticsManager
        self.pending_sequence = None
        self.sequence_start = None
        self.pending_activity = None
        self.activity_start = None

        self.stats.register_session(self)

    def __str__(self):
        return "SessionManager<{}>".format(self.session_id)

    def publish(self, channel, *args, **kwargs):
        kwargs["session_id"] = self.session_id
        return self.run_manager.publish(channel, *args, **kwargs)

    def _evaluate_macros(self, kwargs, context):
        replace_var_macros(kwargs, context)
        return kwargs

    def make_helper(self):
        """Return a :class:`SessionHelper` instance for this session."""
        res = SessionHelper(self)
        return res

    @property
    def browser_session(self):
        """Return a ``requests.Session`` instance for this session."""
        if self._browser_session is None:
            self._browser_session = requests.Session()
        return self._browser_session

    @property
    def context(self):
        return self.context_stack.context

    @property
    def sess_stats(self):
        sess_stats = self.stats["sessions"][self.session_id]
        return sess_stats

    def get_context(self, dotted_key=None, default=NO_DEFAULT):
        res = self.context_stack.get_attr(dotted_key)
        return res

    def get_config(self, dotted_key=None, default=NO_DEFAULT):
        res = self.run_manager.config_manager.get(dotted_key, default)
        return res

    def log_info(self, *args):
        logger.info(self.session_id, *args)
        # self.publish("log", self.session_id, *args, level="info")

    def has_errors(self, or_warnings=False):
        return self.sess_stats["errors"] > 0

    def check_run_limits(self, seq_name):
        """Check if current time or number of errors exceeds the configured limits.

        Args:
            seq_name (str):
                current sequence name. Used to determine if a stopping session
                should still execute the 'end' sequence if the limit was reached
                during a main sequence.
        Returns:
            (bool) false if the current operation should be skipped.
        """
        cs = self._cancelled_seq
        err_limit_reached = (
            # Compare max_errors against global error count
            self.max_errors
            and self.stats.error_count() >= self.max_errors
        )

        run_time = self.run_manager.get_run_time()
        time_limit_reached = self.max_time and run_time > self.max_time

        if not cs and (err_limit_reached or time_limit_reached):
            # We just hit a limit: issue a warning and take a note of the sequence
            self._cancelled_seq = seq_name
            # self.stats.stats["run_limit_reached"] = True
            if err_limit_reached:
                msg = "Reached max. error limit of {}: stopping...".format(
                    self.max_errors
                )
            elif time_limit_reached:
                msg = "Reached max. run time limit of {}: stopping...".format(
                    self.max_time
                )
            self.stats.report_limit_violation(msg)
            logger.warning(yellow(msg))
            return False
        elif cs in ("init", "end"):
            # The limit was reached inside the init or end sequence: always skip
            return False
        elif cs:
            # The limit was reached inside a main sequence: allow to run the end
            # sequence but skip all others
            return seq_name == "end"
        return True

    def report_activity_start(self, sequence, activity):
        """Called by session runner before activities is executed."""
        path = self.context_stack.path()
        self.stats.report_start(self, sequence, activity, path=path)
        logger.info("{} {}".format("DRY-RUN" if self.dry_run else "Execute", path))

    def report_activity_error(self, sequence, activity, activity_args, exc):
        """Called session runner when activity `execute()` or assertions raise an error."""
        # self.stats.inc("errors")

        if isinstance(exc, SkippedError):
            logger.warning(yellow("Skipped {}".format(activity)))
            self.pending_activity = None
            return

        # Create a copy of the current context, so we can shorten values
        context = self.context_stack.context.copy()
        context["last_result"] = shorten_string(context.get("last_result"), 500, 100)

        msg = []
        # msg.append("{} {}: {!r}:".format(self.context_stack, activity, exc))
        # msg.append("{!r}:".format(exc))
        msg.append("{!r}:".format(exc))
        if isinstance(exc, ActivityAssertionError):
            msg.append("Failed assertions:")
            for err in exc.assertion_list:
                msg.append("  - {}".format(err))
        msg.append("Execution path: {}".format(self.context_stack))
        msg.append("Activity: {}".format(activity))
        msg.append("Activity args: {}".format(activity_args))
        msg.append("Context: {}".format(context))

        msg = "\n    ".join(msg)
        logger.error(red(msg))
        self.stats.report_error(self, sequence, activity, error=msg)
        return

    def report_activity_result(self, sequence, activity, activity_args, result, elap):
        """Called session runner when activity `execute()` completes."""
        self.stats.report_end(self, sequence, activity)

    def _process_activity_result(self, activity, activity_args, result, elap):
        """Perform common checks.

        Raises:
            ActivityAssertionError
        """
        context = self.context_stack.context
        errors = []
        # warnings = []

        arg = float(activity_args.get("assert_max_time", 0))
        if arg and elap > arg:
            errors.append(
                "Execution time limit of {} seconds exceeded: {:.3} sec.".format(
                    arg, elap
                )
            )

        arg = activity_args.get("assert_match")
        if arg:
            text = str(result)
            # Note: use re.search (not .match)!
            if not re.search(arg, text, re.MULTILINE):
                errors.append(
                    "Result does not match `{}`: {!r}".format(
                        arg, shorten_string(text, 500, 100)
                    )
                )

        arg = activity_args.get("store_json")
        if arg:
            for var_name, key_path in arg.items():
                try:
                    val = get_dict_attr(result, key_path)
                    context[var_name] = val
                except Exception:
                    errors.append(
                        "store_json could not find `{}` in activity result {!r}".format(
                            key_path, result
                        )
                    )

        if errors:
            raise ActivityAssertionError(errors)
        return

    def run_sequence(self, seq_name, sequence):
        stack = self.context_stack
        context = stack.context

        self.publish(
            "start_sequence", session=self, sequence=sequence, path=stack,
        )
        self.stats.report_start(self, seq_name, None)
        start_sequence = time.monotonic()
        for act_idx, activity_args in enumerate(sequence, 1):
            activity_args = deepcopy(activity_args)
            activity = activity_args.pop("activity")

            # Add activity info to path
            # Note: `get_info()` is not as detailed as it could b, since we don't
            # pass the expanded args here. We set it anyway, so we have a valid
            # stack in case `_evaluate_macros()` blows.
            with stack.enter("#{:02}-{}".format(act_idx, activity.get_info())):

                expanded_args = self._evaluate_macros(activity_args, context)

                # Let activity do internal calculations, that might be used by
                # the follwing call to `get_info()`
                activity.prepare_execute(self, **expanded_args)

                # Enhance the path info with expanded args
                stack.set_last_part(activity.get_info(expanded_args=expanded_args))

                error = None
                result = None
                self.publish(
                    "start_activity",
                    session=self,
                    sequence=sequence,
                    activity=activity,
                    expanded_args=expanded_args,
                    context=context,
                    path=stack,
                )
                start_activity = time.monotonic()

                self.report_activity_start(seq_name, activity)

                try:
                    if self.stop_request.is_set():
                        raise StoppedError
                    if not self.check_run_limits(seq_name):
                        raise SkippedError

                    result = activity.execute(self, **expanded_args)
                    context["last_result"] = result
                    # Evaluate standard `assert_...` and `store_...` clauses:
                    elap = time.monotonic() - start_activity
                    self._process_activity_result(
                        activity, activity_args, result, elap,
                    )
                    self.report_activity_result(
                        seq_name, activity, activity_args, result, elap,
                    )
                except (Exception, KeyboardInterrupt) as e:
                    if isinstance(e, KeyboardInterrupt):
                        self.stop_request.set()
                    error = e
                    self.report_activity_error(seq_name, activity, activity_args, e)
                    if not isinstance(e, (KeyboardInterrupt, StressorError)):
                        logger.exception("")
                    # return False

                finally:
                    elap = time.monotonic() - start_activity
                    self.publish(
                        "end_activity",
                        session=self,
                        sequence=sequence,
                        path=stack,
                        activity=activity,
                        result=result,
                        error=error,
                        elap=elap,
                        context=context,
                    )

        elap = time.monotonic() - start_sequence
        self.stats.report_end(self, seq_name, None)
        self.publish(
            "end_sequence", session=self, sequence=sequence, path=stack, elap=elap,
        )
        context["last_result"] = None
        return not self.has_errors()

    def run(self):
        stack = self.context_stack
        rm = self.run_manager
        config_manager = rm.config_manager
        config = config_manager.config
        sequences = config_manager.sequences
        scenario = config_manager.scenario
        sessions = config_manager.sessions
        session_duration = float(sessions.get("duration", 0))

        self.publish("start_session", session=self)
        self.stats.report_start(self, None, None)

        start_session = time.monotonic()
        skip_all = False
        skip_all_but_end = False

        for seq_idx, seq_def in enumerate(scenario, 1):
            seq_name = seq_def["sequence"]
            if skip_all or (skip_all_but_end and seq_name != "end"):
                logger.warning("Skipping sequence '{}'.".format(seq_name))
                continue

            sequence = sequences.get(seq_name)
            loop_repeat = int(seq_def.get("repeat", 0))
            loop_duration = float(seq_def.get("duration", 0))
            start_seq_loop = time.monotonic()
            loop_idx = 0
            while True:
                loop_idx += 1
                if not self.check_run_limits(seq_name=seq_name):
                    skip_all_but_end = True
                    break
                # One single pass by default
                if not loop_repeat and not loop_duration and loop_idx > 1:
                    break
                # `Sequence repeat: COUNT`:
                if loop_repeat and loop_idx > loop_repeat:
                    break
                # `--single`:
                if loop_idx > 1 and config.get("force_single"):
                    logger.warning(
                        "force_single: sequence '{}' skipping remaining {} loops.".format(
                            seq_name, loop_repeat - 1 if loop_repeat else ""
                        )
                    )
                    break

                now = time.monotonic()
                # `Sequence duration: SECS`:
                if loop_duration > 0 and now > (start_seq_loop + loop_duration):
                    logger.info(
                        "Stopping sequence '{}' loop after {} sec.".format(
                            seq_name, loop_duration
                        )
                    )
                    break
                # `Session duration: SECS` (but run 'end' sequence):
                elif (
                    seq_name != "end"
                    and session_duration > 0
                    and now > (start_session + session_duration)
                ):
                    logger.info(
                        "Stopping scenario '{}' loop after {} sec.".format(
                            seq_name, session_duration
                        )
                    )
                    skip_all_but_end = True
                    break

                with stack.enter("#{:02}-{}@{}".format(seq_idx, seq_name, loop_idx)):
                    is_ok = self.run_sequence(seq_name, sequence)
                    if seq_name == "init" and not is_ok:
                        logger.error(
                            "Stopping scenario due to an error in the 'init' sequence."
                        )
                        skip_all = True
                        break
                    elif self.stop_request.is_set():
                        logger.error("Stopping scenario due to a stop request.")
                        # TODO: a second 'ctrl-c' should not be so graceful
                        skip_all_but_end = True
                        break
            # self.stats.report_end(self, seq_name, None)

        elap = time.monotonic() - start_session
        self.stats.report_end(self, None, None)

        self.publish("end_session", session=self, elap=elap)

        # if self._cancelled_seq:
        #     return False
        return not self.has_errors()
