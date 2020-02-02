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
        global_vars = {
            # "foo": 41,
            # "__builtins__": {},
        }
        # local_vars = session.context
        local_vars = session.context.copy()
        assert "result" not in local_vars
        assert "session" not in local_vars
        local_vars["session"] = session.make_helper()

        # prev_local_keys = set(locals())
        prev_global_keys = set(globals())
        prev_context_keys = set(local_vars.keys())

        try:
            exec(self.script, global_vars, local_vars)
        except ConnectionError as e:
            # TODO: more requests-exceptions?
            msg = "Script failed: {!r}: {}".format(e, e)
            raise ScriptActivityError(msg)
        except Exception as e:
            msg = "Script failed: {!r}: {}".format(e, e)
            if session.verbose >= 4:
                logger.exception(msg)
                raise ScriptActivityError(msg) from e
            raise ScriptActivityError(msg)
        finally:
            local_vars.pop("session")

        result = local_vars.pop("result", None)

        context_keys = set(local_vars.keys())
        new_keys = context_keys.difference(prev_context_keys)

        if new_keys:
            if self.export is None:
                logger.info(
                    "Skript activity has no `export` defined. Ignoring new variables: '{}'".format(
                        "', '".join(new_keys)
                    )
                )
            else:
                for k in self.export:
                    v = local_vars.get(k)
                    assert type(v) in (int, float, str, list, dict)
                    session.context[k] = v
                    logger.debug("Set context.{} = {!r}".format(k, v))
                # store_keys = new_keys.intersection(self.export)

        # TODO: this cannot happen?
        new_globals = set(globals().keys()).difference(prev_global_keys)
        if new_globals:
            logger.warning("Script-defined globals: {}".format(new_globals))
            raise ScriptActivityError("Script introduced globals")

        # new_context = context_keys.difference(prev_context_keys)
        # logger.info("Script-defined context-keys: {}".format(new_context))

        # new_locals = set(locals().keys()).difference(prev_local_keys)
        # if new_locals:
        #     logger.info("Script-defined locals: {}".format(new_locals))

        # logger.info("Script locals:\n{}".format(pformat(local_vars)))
        if expanded_args.get("debug") or session.verbose >= 5:
            logger.info(
                "{} {}\n  Ccontext after execute:\n    {}\n  return value: {!r}".format(
                    session.context_stack,
                    self,
                    pformat(session.context, indent=4),
                    result,
                )
            )
        return result
