# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
import random
from textwrap import dedent

import yaml

from stressor.plugins.base import ActivityBase, MacroBase
from stressor.util import check_arg, format_elap


class LoadMacro(MacroBase):
    """Implement `$load(path)` macro."""

    def apply(self, config_manager, parent, parent_key, path):
        path = config_manager.resolve_path(path, must_exist=True)

        if path.lower().endswith(".py"):
            assert parent_key == "script"
            with open(path, "rt") as f:
                res = f.read()
            parent[parent_key] = res
            return res

        if not path.lower().endswith((".yaml", ".yml")):
            raise NotImplementedError
        # Load (and )
        with open(path, "rt") as f:
            res = yaml.safe_load(f)
        assert isinstance(parent, dict)
        assert isinstance(res, list)
        parent[parent_key] = res
        # print(yaml.dump(parent, default_flow_style=False))
        return res


class EnvMacro(MacroBase):
    """Implement `$env(var_name)` macro, which resolves an environment variable at load-time."""

    def apply(self, config_manager, parent, parent_key, var_name):
        # TODO:
        # Allow optional 'default' args: `$env(HOME, Foo)`
        # Maybe introspection can automate this?
        # var_name, default = parse_arglist(var_name)
        res = os.environ[var_name]
        parent[parent_key] = res


class DebugMacro(MacroBase):
    """Implement `$debug()` macro, which dumps information at run-time."""

    def apply(self, config_manager, parent, parent_key, var_name):
        parent[parent_key] = "RunScript"
        parent["name"] = "$debug"
        parent["export"] = []
        parent["script"] = dedent(
            r"""
            from pprint import pprint
            pprint(locals())
        """
        )


# class CrontabMacro(MacroBase):
#     """Implement `$cron()` macro, which inserts the current UTC time stamp.

#     https://github.com/josiahcarlson/parse-crontab
#     """

#     def apply(self, config_manager, parent, parent_key, var_name):
#         raise NotImplementedError


# class StampMacro(MacroBase):
#     """Implement `$stamp()` macro, which inserts the current UTC time stamp."""

#     run_time_eval = True

#     def apply(self, config_manager, parent, parent_key, var_name):
#         raise NotImplementedError


# class StopMacro(MacroBase):
#     """Implement `$stop()` macro, which dumps information at run-time and ends execution."""

#     def apply(self, config_manager, parent, parent_key, var_name):
#         raise NotImplementedError


# class BreakMacro(MacroBase):
#     """Implement `$break()` macro, which halts and enters single-step mode."""

#     def apply(self, config_manager, parent, parent_key, var_name):
#         # dump info
#         # enter single-step mode
#         # allow to stop the run
#         raise NotImplementedError


class SleepMacro(MacroBase):
    """Implement `$sleep(duration)` macro, which is a shortcut to :class`SleepActivity`."""

    _args_def = (
        ("min", float),  # mandatory
        ("max", float, None),  # optional
    )

    def apply(self, config_manager, parent, parent_key, min, max):
        # duration is always a  string, it may even be $(context.var) macro.
        # We still do some checking here, to get early load-time errors.
        # check_arg(min, str)

        assert parent_key == "activity"
        # if "$" not in min:
        #     assert_always(float(min) >= 0)

        parent[parent_key] = "Sleep"
        parent["duration"] = min
        if max is not None:
            parent["duration_2"] = max

        return True


class SleepActivity(ActivityBase):
    """
    Args:
        duration (float): sleep duration in seconds

    Examples::

        sequences:
          main
            - activity: Sleep
              duration: 0.5
    """

    _mandatory_args = {"duration"}
    _known_args = {"duration", "duration_2"}
    _info_args = ("name", "duration", "duration_2")

    #: Sleep activities are ignorable by default
    _default_ignore_timing = True

    def __init__(self, config_manager, **activity_args):
        check_arg(activity_args.get("duration"), (str, int, float))
        check_arg(activity_args.get("duration_2"), (str, int, float), or_none=True)

        #: Set while sleeping, to enhance the info string
        self._cur_duration = None

        super().__init__(config_manager, **activity_args)

        # TODO: Support CronTab syntax
        #     https://github.com/taichino/croniter
        #     https://github.com/josiahcarlson/parse-crontab

        # check_arg(duration, (float, int, str))

    # def __str__(self):
    #     return "Sleep({:.3} sec.)".format(self.duration)

    def get_info(self, info_args=True, expanded_args=None):
        if (
            self._cur_duration and expanded_args and "duration_2" in expanded_args
        ):  # Set by prepare_execute()
            return "{}(duration[{}..{}] => {})".format(
                self.get_script_name(),
                float(expanded_args["duration"]),
                float(expanded_args["duration_2"]),
                format_elap(self._cur_duration),
            )
        return super().get_info(info_args, expanded_args)

    def prepare_execute(self, session, **expanded_args):
        duration = float(expanded_args["duration"])
        duration_2 = expanded_args.get("duration_2")
        if duration_2 is not None:
            duration = random.uniform(duration, float(duration_2))
        self._cur_duration = duration

    def execute(self, session, **expanded_args):
        # duration = float(expanded_args["duration"])
        # duration_2 = expanded_args.get("duration_2")
        # if duration_2 is not None:
        #     duration = random.uniform(duration, float(duration_2))
        assert self._cur_duration is not None
        duration = self._cur_duration
        self._cur_duration = None
        if not session.dry_run:
            session.stop_request.wait(timeout=duration)
        return


# class MemoryActivity(ActivityBase):
#     """
#     Args:
#         operation (str): 'alloc' | 'free'
#         size (int):
#     """

#     def __init__(self, config_manager, operation, **activity_args):
#         super().__init__(config_manager, **activity_args)

#     def execute(self, session):
#         raise NotImplementedError


# class CpuActivity(ActivityBase):
#     """
#     Args:
#         operation (str): 'load' | 'stop'
#         cores (int): Default: 1
#         async (bool): Default: True
#         duration (float):
#     """

#     def __init__(self, config_manager, operation, **activity_args):
#         super().__init__(config_manager, **activity_args)

#     def execute(self, session):
#         raise NotImplementedError


# class FileActivity(ActivityBase):
#     """
#     Args:
#         operation (str): 'read' | 'write'
#         size (int):
#         path (str):
#     """

#     def __init__(self, config_manager, operation, **activity_args):
#         super().__init__(config_manager, **activity_args)

#     def execute(self, session):
#         raise NotImplementedError
