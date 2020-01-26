# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pprint import pformat
from textwrap import dedent

from stressor.plugins.base import (
    ActivityBase,
    ActivityCompileError,
    ScriptActivityError,
)
from stressor.util import check_arg, logger, shorten_string


class RunScriptActivity(ActivityBase):
    def __init__(
        self, config_manager, path=None, script=None, export=None, **activity_args
    ):
        """"""
        self.compile_path = config_manager.stack
        # check_arg(path, str, or_none=True)
        check_arg(
            script, str, or_none=True, condition=path is not None or script is not None
        )
        check_arg(export, (str, list, tuple), or_none=True)
        if path:
            if script:
                raise ActivityCompileError(
                    "`path` and `script` args are mutually exclusive"
                )
            path = config_manager.resolve_path(path)
            with open(path, "rt") as f:
                script = f.read()
            #:
            self.script = compile(script, path, "exec")
        elif script:
            # script = dedent(self.script)
            self.script = compile(script, "<string>", "exec")
        else:
            raise ActivityCompileError("Either `path` or `script` expected")

        #: Store a shortened code snippet for debug output
        self.source = shorten_string(dedent(script), 200)
        # print(self.source)

        if export is None:
            self.export = None
        elif isinstance(export, str):
            self.export = set((export,))
        else:
            self.export = set(export)

        self.raw_args = activity_args

    def execute(self, session, **expanded_args):
        """"""
        # script = self.script
        export = self.export
        global_vars = {
            # "foo": 41,
            # "__builtins__": {},
        }
        local_vars = session.context
        # local_vars = session.context.copy()

        prev_local_keys = set(locals())
        prev_global_keys = set(globals())
        prev_context_keys = set(local_vars.keys())

        try:
            exec(self.script, global_vars, local_vars)
        except Exception as e:
            msg = "Script failed: {!r}: {}".format(e, e)
            logger.exception(msg)
            raise ScriptActivityError(msg) from e

        context_keys = set(local_vars.keys())
        if self.export is None:
            pass
        else:
            new_keys = context_keys.difference(prev_context_keys)
            store_keys = new_keys.intersection(self.export)

        logger.info(
            "Script defined context-keys: {}".format(
                context_keys.difference(prev_context_keys)
            )
        )
        logger.info(
            "Script defined globals: {}".format(
                set(globals().keys()).difference(prev_global_keys)
            )
        )
        logger.info(
            "Script defined locals: {}".format(
                set(locals().keys()).difference(prev_local_keys)
            )
        )
        # logger.info("Script locals:\n{}".format(pformat(local_vars)))
        if session.verbose >= 5:
            logger.debug(
                "{} {} context after exectute:\n{}".format(
                    session.context_stack, self, pformat(locals())
                )
            )
        return local_vars.get("last_result")
