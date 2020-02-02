# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from textwrap import dedent

import yaml

from stressor.plugins.base import ActivityBase, MacroBase
from stressor.util import assert_always, check_arg


class LoadMacro(MacroBase):
    """Implment `$load(path)` macro."""

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
    """Implment `$env(var_name)` macro, which resolves an environment variable at load-time."""

    def apply(self, config_manager, parent, parent_key, var_name):
        # TODO:
        # Allow optional 'default' args: `$env(HOME, Foo)`
        # Maybe introspection can automate this?
        # var_name, default = parse_arglist(var_name)
        res = os.environ[var_name]
        parent[parent_key] = res


class DebugMacro(MacroBase):
    """Implment `$debug()` macro, which dumps information at run-time."""

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
#     """Implment `$cron()` macro, which inserts the current UTC time stamp.

#     https://github.com/josiahcarlson/parse-crontab
#     """

#     def apply(self, config_manager, parent, parent_key, var_name):
#         raise NotImplementedError


# class StampMacro(MacroBase):
#     """Implment `$stamp()` macro, which inserts the current UTC time stamp."""

#     run_time_eval = True

#     def apply(self, config_manager, parent, parent_key, var_name):
#         raise NotImplementedError


# class StopMacro(MacroBase):
#     """Implment `$stop()` macro, which dumps information at run-time and ends execution."""

#     def apply(self, config_manager, parent, parent_key, var_name):
#         raise NotImplementedError


# class BreakMacro(MacroBase):
#     """Implment `$break()` macro, which halts and enters single-step mode."""

#     def apply(self, config_manager, parent, parent_key, var_name):
#         # dump info
#         # enter single-step mode
#         # allow to stop the run
#         raise NotImplementedError


class SleepMacro(MacroBase):
    """Implment `$sleep(duration)` macro, which is a shortcut to :class`SleepActivity`."""

    #: Sleep activities are ignorable by default
    _default_ignore_timing = True

    def apply(self, config_manager, parent, parent_key, duration):
        # duration is always a  string, it may even be $(context.var) macro.
        # We still do some checking here, to get early load-time errors.
        check_arg(duration, str)

        assert parent_key == "activity"
        if "$" not in duration:
            assert_always(float(duration) >= 0)

        parent[parent_key] = "Sleep"
        parent["duration"] = duration
        return True


class SleepActivity(ActivityBase):
    """
    Args:
        duration (float): sleep duration in seconds

    Examples:

        ```yaml
        sequences:
          main
            - activity: Sleep
              duration: 0.5
        ```
    """

    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, **activity_args)

        # TODO: allow random range tuple: (min, max)

        # TODO: Support CronTab syntax
        #     https://github.com/taichino/croniter
        #     https://github.com/josiahcarlson/parse-crontab

        # check_arg(duration, (float, int, str))

    # def __str__(self):
    #     return "Sleep({:.3} sec.)".format(self.duration)

    def execute(self, session, **expanded_args):
        # session.report_activity(self, True, "Sleep({:.3} sec)".format(self.duration))
        duration = float(expanded_args["duration"])
        if not session.dry_run:
            session.stop_request.wait(timeout=duration)


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
