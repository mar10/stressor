# -*- coding: utf-8 -*-
# (c) 2020-2023 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pathlib import Path
from pprint import pformat
from textwrap import dedent
import sqlite3

from stressor.plugins.base import (
    ActivityBase,
    ActivityCompileError,
    ScriptActivityError,
)
from stressor.util import NO_DEFAULT, check_arg, logger, shorten_string


# TODO: request sessions
class ReportActivity(ActivityBase):
    _mandatory_args = {"format", "path"}
    _known_args = {"columns", "tablename"}
    _info_args = ("name", "path")
    _default_ignore_timing = True  # not considerd for net timings

    def __init__(self, config_manager, **activity_args):
        """"""
        super().__init__(config_manager, **activity_args)

        path = Path(activity_args.get("path"))
        path = config_manager.resolve_path(path)

        format = activity_args.get("format")
        columns = activity_args.get("columns")
        tablename = activity_args.get("tablename")

        self.database = None
        if format == "csv":
            check_arg(columns, list, condition=columns)
        elif format == "sqlite":
            check_arg(tablename, str, condition=tablename)
            self.database = sqlite3.connect(path)
        else:
            raise ValueError(f"Unknown format {format!r}: expected 'csv' or 'sqlite'.")

        return

    def execute(self, session, **expanded_args):
        """"""
        global_vars = {
            # "foo": 41,
            # "__builtins__": {},
        }
        # local_vars = session.context
        local_vars = session.context.copy()
        assert "result" not in local_vars
        assert "session" not in local_vars
        local_vars["session"] = session.make_session_helper()

        # prev_local_keys = set(locals())
        prev_global_keys = set(globals())
        prev_context_keys = set(local_vars.keys())

        try:
            exec(self.script, global_vars, local_vars)
        except Exception as e:
            msg = "Script failed: {!r}: {}".format(e, e)
            if session.verbose >= 4:
                logger.debug(msg)
                raise ScriptActivityError(msg) from e
            raise ScriptActivityError(msg)
        finally:
            local_vars.pop("session")

        result = local_vars.pop("result", None)

        context_keys = set(local_vars.keys())
        new_keys = context_keys.difference(prev_context_keys)

        # TODO: this cannot happen?
        new_globals = set(globals().keys()).difference(prev_global_keys)
        if new_globals:
            logger.warning("Script-defined globals: {}".format(new_globals))
            raise ScriptActivityError("Script introduced globals")

        # logger.info("Script locals:\n{}".format(pformat(local_vars)))
        if expanded_args.get("debug") or session.verbose >= 5:
            logger.info(
                "{} {}\n  Context after execute:\n    {}\n  return value: {!r}".format(
                    session.context_stack,
                    self,
                    pformat(session.context, indent=4),
                    result,
                )
            )
        elif session.verbose >= 3 and result is not None:
            logger.info(
                "{} returnd: {!r}".format(
                    session.context_stack,
                    shorten_string(result, 200) if isinstance(result, str) else result,
                )
            )

        return result
