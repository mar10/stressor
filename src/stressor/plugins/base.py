# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re
from abc import ABC, abstractmethod

from stressor.util import (
    StressorError,
    assert_always,
    check_arg,
    logger,
    parse_args_from_str,
)

#: (dict) Currently known activity classes by their script name,
#: e.g. {'GetRequest': GetRequestActivity, ...}
#: (Call :func:`register_activity_plugins()` to update this map after new plugins
#: have been imported.)
activity_plugin_map = {}

#: (dict) Currently known macro classes by their script name,
#: e.g. {'load': LoadMacro, ...}
#: (Call :func:`register_macro_plugins()` to update this map after new plugins
#: have been imported.)
macro_plugin_map = {}

#: (set) all activities accept these arguments
common_args = set(
    (
        "activity",
        "assert_match",
        "assert_max_time",
        "debug",
        "mock_result",
        "monitor",
        "name",
    )
)


def register_plugins():
    register_activity_plugins()
    register_macro_plugins()


class ActivityError(StressorError):
    """Base for all errors that are explicitly raised by activities."""


class ActivityTimeoutError(ActivityError):
    """Activity timed out."""


class ActivityCompileError(ActivityError):
    """Raised when activity constructor fails."""


class ActivityAssertionError(ActivityError):
    """Assertion failed (e.g. `assert_match` argument, ...)."""

    def __init__(self, assertion_list):
        super().__init__("Activity assertion failed")
        check_arg(assertion_list, (str, list))
        if isinstance(assertion_list, str):
            assertion_list = [assertion_list]
        self.assertion_list = assertion_list


class ScriptActivityError(ActivityError):
    """Raised when a ScriptActivity fails."""


class ActivityBase(ABC):
    """
    Common base class for all activities.

    New activity plugins can be created by deriving from this class,
    importing it, and then calling :func:`register_activity_plugins()`.

    Names of derived classes should end with '...Activity'.
    Classes which names that begin with an underscore ('_') are ignored.
    """

    #: (str) Name by which the actvity can be used in YAML configurations.
    #: Defaults to class name without trailing `...Activity`, e.g.
    #: 'SleepActivity' is called as ``activity: Sleep``
    _script_name = None

    #: (set) If defined, the default implementation of `compile()` will raise
    #: an error if any of those args is not passed.
    _mandatory_args = None

    #: (set) If defined, the default implementation of `compile()` will raise
    #: an error if other args are passed to the constructor.
    _known_args = None

    #: (set) Internal use only!
    _all_known_args = None

    #: (tuple|None) List of argument names that will be displayed in path
    #: strings
    _info_args = None

    #: (bool)
    _default_monitor = False

    #: (bool)
    _default_ignore_timing = False

    @abstractmethod
    def __init__(self, config_manager, **activity_args):
        """
        The constructor is called by the :class:`ConfigManager`, when the
        configuration was read.

        The compiler replaces the activity name in the definition's `activity`
        attribute with this instance.
        The `execute()` method is then called by the session runner on or more
        times.
        The default implementation stores `activity_args` as `self.raw_args`.
        however derived classes may choose to add named args explicitly for
        better readability and checking.

        An implementation should

            - Check args and raise errors, so we get early load-time failures
              when the configuration is read and compiled.
            - Optionally cache some information in this instance that can be
              re-used in the execute calls.
            - Optionally call `compiler.add_warning()`

        Attributes:
            compile_path_short (str):
                Path to location of definition in the configuration, e.g.
                '/main/2/PutRequest'
            compile_path (str):
                Path to location of definition in the configuration with
                added argument infos, e.g.
                '/main/2/PutRequest($(base_url)/test.html)'
            raw_args (dict):
            monitor (bool):
            ignore_timing (bool):
        Args:
            compile_path (:class:`PathStack`):
                The location breadcrumb path of this activity in the configration
                structure, e.g. 'main/#4'.
            activity_args (dict):
                named arguments that were passed to the activity definition.
                Note that the arguments are read at load-time and are not yet
                expanded (i.e. may contain `$(context_var)` macros).
        """
        self.raw_args = activity_args
        self.compile_path_short = config_manager.stack.get_path(
            skip_segs=2, last_seg=self.get_script_name()
        )
        self.compile_path = config_manager.stack.get_path(
            skip_segs=2, last_seg=self.get_info()
        )
        passed = set(activity_args.keys())
        if self._mandatory_args:
            missing = self._mandatory_args.difference(passed)
            if missing:
                raise ActivityCompileError(
                    "Missing mandatory arguments: {}".format(missing)
                )

        if self._all_known_args is None:
            if self._known_args:
                self._all_known_args = common_args | self._known_args
            else:
                self._all_known_args = common_args

        extra = passed.difference(self._all_known_args)
        if extra:
            raise ActivityCompileError("Unsupported arguments: {}".format(extra))

        self.monitor = activity_args.get("monitor", self._default_monitor)
        self.ignore_timing = activity_args.get(
            "ignore_timing", self._default_ignore_timing
        )

    def __str__(self):
        """Return a descriptive string."""
        return self.get_info()

    @classmethod
    def get_script_name(cls):
        # Note: we must check `cls.__dict__` instead of `cls._script_name`,
        # because we want to test the local class attribute (not a derived one):
        if cls.__dict__.get("_script_name") is None:
            assert_always(cls.__name__.endswith("Activity"))
            cls._script_name = cls.__name__[:-8]
        return cls._script_name

    def get_info(self, info_args=True, expanded_args=None):
        """Return a descriptive string (optionally using expanded args).

        Args:
            info_args (tuple|bool):
                List of argument names that should be added to display string.
                True: default to `self._info_args` (see `None` by default)
                False: don't add arguments
                None: all arguments
            expanded_args (dict, optional):
                optional argment dict (defaults to `self.raw_args`)
        """
        if info_args is True:
            info_args = self._info_args
        elif info_args is False:
            info_args = []
        arg_dict = self.raw_args if expanded_args is None else expanded_args
        if info_args:
            # Add selected args
            args = (
                "{}={!r}".format(a, arg_dict.get(a)) for a in info_args if a in arg_dict
            )
        else:  # add all args
            args = (
                "{}={!r}".format(*kv) for kv in arg_dict.items() if kv[0] != "activity"
            )
        return "{}({})".format(self.get_script_name(), ", ".join(args))

    def prepare_execute(self, session, **expanded_args):
        """Allow an activity to prepare the next execution.

        The session manager calls this for every activity instance, directly
        before `get_info()` and `execute()`.
        Normally this method does not need to be implemented. (One exception is
        `SleepActivity`, that calculates the next random duration, so it can
        be displayed by `get_info()`.)
        """
        pass

    @abstractmethod
    def execute(self, session, **expanded_args):
        """
        Called by the :class:`SessionManager`, after `$(context.var)` macros
        have been resolved if any.
        A derived class MUST implement this method.

        The session manager calls this methods for every activity instance:

        1. prepare_execute()
        2. get_info()
        3. execute()

          - Call session.log_warning()
          - raise ActivityError() for errors that a user can ignore by --force flag
          - Honor session.stop_request
          - Honor session.dry_run

        Args:
            session (:class:`SessionManager`):
            expanded_args (dict):
                current global vars
        Raises:
            ActivityError:
            Exception: all other exceptions are considered a fatal error
        Returns:
            nothing
        """


def register_activity_plugins():
    """Register currently loaded activity plugins.

    These are all currently known subclasses of :class:`stressor.plugins.ActivityBase`.
    """
    # Import stock class definitions, so we can scan the subclasses
    import stressor.plugins.common  # noqa F401
    import stressor.plugins.http_activities  # noqa F401
    import stressor.plugins.script_activities  # noqa F401

    def _add(cls):
        for act_cls in cls.__subclasses__():
            name = act_cls.get_script_name()
            # print("register" ,act_cls, name)
            assert_always(
                macro_plugin_map.get(name) in (None, act_cls),
                "Class name conflict: {}".format(act_cls),
            )
            if not name.startswith("_"):
                activity_plugin_map[name] = act_cls
            _add(act_cls)

    _add(ActivityBase)
    logger.debug("Registered activity plugins:\n{}".format(activity_plugin_map))


class MacroBase(ABC):
    """
    Common base class for all load-time script macros of the form ``$NAME(ARGS)``.

    These macros are applied at load time to the nested dict that was read from
    a YAML file.
    Typically they replace the value of that dict element (``parent[parent_key]``)
    with new content.

    For example

      - ``$load(PATH)`` replaces the element with a parsed YAML content or
        the text content of a python file.
      - ``$sleep(DURATION)`` replaces the element with a :class:`SleepActivity`
        definition

    Note that context variable expansions of the form ``$(CONTEXT.VAR.NAME)``
    are *not* handled by this kind of macro, because this has to be dealt with
    at run time.

    TODO: This means that ARGS cannot be dynamic, so for example $load($(my_file_name))
    will not work.

    Custom macro plugins can be defined by deriving from this class, importing
    it, and then calling :func:`register_macro_plugins()`.
    """

    #: Name for use in scripts.
    #: Defaults to lowercase class name without trailing `...Macro`, e.g.
    #: 'LoadMacro' is exposed as ``$load(...)``
    _script_name = None
    #: Regular expression that extracts '$NAME(ARGS)'
    #: Defaults to ...
    _regex = None
    #: List of tuples that define the supported positional arguments and
    #: optional default values.
    #: See :func:`stressor.util.parse_args_from_str` for syntax.
    #: If `None`, the raw cotent inside the brackets is passed as single string .
    _args_def = None

    #: Allow late evaluation (e.g. $stamp)
    #: TODO: Not yet implemented
    run_time_eval = False

    def __init__(self, **macro_args):
        """"""

    @classmethod
    def get_script_name(cls):
        # Note: we must check `cls.__dict__` instead of `cls._script_name`,
        # because we want to test the local class attribute (not a derived one):
        if cls.__dict__.get("_script_name") is None:
            assert_always(cls.__name__.endswith("Macro"))
            cls._script_name = cls.__name__[:-5].lower()
        return cls._script_name

    @classmethod
    def get_regex(cls):
        if cls._regex is None:
            name = cls.get_script_name()
            cls._regex = re.compile(r"\s*\$" + name + r"\((.*)\)\s*")
        return cls._regex

    def match_apply(self, context_reader, parent, parent_key):
        """Parse current value and call self.apply() if the macro matches.

        This default implementation supports
        Returns:
            (bool, any) (handled, )
        """
        pattern = self.get_regex()
        value = parent[parent_key]
        match = pattern.match(value)
        if not match:
            return (False, None)
        args = match.groups()
        assert len(args) == 1
        arg_str = args[0]
        if self._args_def:
            kwargs = parse_args_from_str(arg_str, self._args_def)
            res = self.apply(context_reader, parent, parent_key, **kwargs)
        else:
            res = self.apply(context_reader, parent, parent_key, arg_str)
        # logger.debug("Eval {}: {} => {}".format(stack, value, res))
        return (True, res)

    @abstractmethod
    def apply(self, context_reader, parent, parent_key, args_str):
        """
        Args:
            context_reader (:class:`ConfigManager`):
            parent (dict|list):
            parent_key (str|int):
            args_str (str|**kwargs):
        Returns:
            (any) The result that was produced (and stored into `parent[parent_key]`)
        """


def register_macro_plugins():
    """Register currently loaded macro plugins.

    These are all currently known subclasses of :class:`~stressor.plugins.MacroBase`.
    """
    # Import stock class definitions, so we can scan the subclasses
    import stressor.plugins.common  # noqa F401

    def _add(cls):
        for macro_cls in cls.__subclasses__():
            name = macro_cls.get_script_name()
            assert_always(
                macro_plugin_map.get(name) in (None, macro_cls),
                "Class name conflict: {}".format(macro_cls),
            )
            if not name.startswith("_"):
                macro_plugin_map[name] = macro_cls
            _add(macro_cls)

    _add(MacroBase)
    logger.debug("Registered macro plugins:\n{}".format(macro_plugin_map))
