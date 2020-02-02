# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
import re

import yaml

from stressor.deep_dict import get_dict_attr
from stressor.plugins.base import (
    ActivityBase,
    activity_plugin_map,
    macro_plugin_map,
    register_plugins,
)
from stressor.util import PathStack, StressorError, assert_always, check_arg, logger

# DEFAULT_RUN_FILE = "project.yaml"
VAR_MACRO_REX = re.compile(r"\$\(\s*(\w[\w.:]*)\s*\)")
GENERIC_MACRO_REX = re.compile(r"\$\w+.*\(.*\).*")


class ConfigurationError(StressorError):
    """"""


def replace_var_macros(value, context):
    """
    Replace all macros of type `$(CONTEXT.VAR.NAME)`.
    """
    stack = PathStack()

    def repl(value, context, parent, parent_key):
        with stack.enter(str(parent_key or "?")):
            if isinstance(value, dict):
                for key, sub_val in value.items():
                    repl(sub_val, context, value, key)
            elif isinstance(value, (list, tuple)):
                for idx, elem in enumerate(value):
                    repl(elem, context, value, idx)
            elif isinstance(value, str):
                org_value = value
                if "$" in value and str(stack) == "/?/script":
                    # Don't replace macros inside RunActivity scripts
                    logger.debug("Not replacing macros inside `script`s.")
                    return value
                while "$" in value:
                    found_one = False
                    temp_val = value
                    for match in VAR_MACRO_REX.finditer(temp_val):
                        found_one = True
                        # print(match, match.groups())
                        macro, var_name = match.group(), match.groups()[0]
                        # resolve dotted names:
                        # var_value = context[var_name]
                        try:
                            var_value = get_dict_attr(context, var_name)
                            value = value.replace(macro, var_value)
                        except (KeyError, TypeError):
                            raise RuntimeError(
                                "Error evaluating {}: '{}': '{}' not found in context or None.".format(
                                    stack, org_value, var_name
                                )
                            )
                    if not found_one:
                        break
                parent[parent_key] = value
        return value

    res = repl(value, context, None, None)
    return res


register_plugins()


class ConfigManager:
    """
    Define and validate a run-configuration.
    Also reads and compiles YAML files.
    """

    #: Currently supportted syntax version.
    #: (Incremented when incompatible changes are introduced.)
    FILE_VERSION = 0

    def __init__(self, stats_manager):
        #: (dict) The complete parsed YAML file as dict
        self.stats_manager = stats_manager
        #: (dict) The complete parsed YAML file as dict
        self.config_all = None
        #: (int) The file version, parsed from the `filer_version#VERSION` tag
        self.file_version = None
        #: (str) Absolute path of the YAML file
        self.path = None
        #: (str) Absolute root folder of the YAML file
        self.root_folder = None
        #: (str) Shortcut to self.run_config["name"] (defsaults to filename without extension)
        self.name = None
        # #: (dict) shortcut to config_all["run_config"]
        # self.run_config = None
        # #: (dict) shortcut to config_all["run_config"]["context"]
        # self.context = None
        # #: (dict) shortcut to config_all["sequences"]
        # self.sequences = None
        #: (PathStack) Current compile location
        self.stack = None
        #: (dict) lists of compile errors and warnings
        self.results = {
            "error": [],
            "warning": [],
        }

        # if path is not None:
        #     self.read(path)
        return

    def resolve_path(self, path, must_exist=True, check_root=True, default_ext=None):
        """Return an absolute path, assuming relative to the original config file."""
        # TODO: check for invalid access (security risk!)
        assert_always(self.path, "`read()` must be called before")
        if not path.startswith("/"):
            path = os.path.join(self.root_folder, path)
        path = os.path.abspath(path)
        if check_root and not path.startswith(self.root_folder):
            raise ValueError(
                "Path must be in or below {}: {}".format(self.root_folder, path)
            )
        if must_exist and not os.path.isfile(path):
            raise ValueError("File not found: {}".format(path))
        return path

    def report_error(self, msg, level="error", exc=None, stack=None):
        """Called by activity and macro constructors to signal errors or warnings.

        The compiler also calls this when a constructor raises an exception.
        """
        check_arg(level, str, level in ("error", "warning"))
        path = stack if stack else str(self.stack)

        hint = "{}: {}".format(path, msg)
        if exc:
            logger.exception(hint)
        elif level == "warning":
            logger.warning(hint)
        else:
            logger.error(hint)

        self.results[level].append({"msg": msg, "path": path})

    @property
    def run_config(self):
        """shortcut to config_all["run_config"]."""
        return self.config_all["run_config"]

    @property
    def context(self):
        """shortcut to config_all["context"]."""
        return self.run_config["context"]

    @property
    def sequences(self):
        """shortcut to config_all["sequences"]."""
        return self.config_all["sequences"]

    def has_errors(self, or_warnings=False):
        return bool(self.results["error"] or (or_warnings and self.results["warning"]))

    # def format_result(self):
    #     res = []
    #     if self.results["error"]:
    #         res.append("Compile errors:")
    #         for m in self.results["error"]:
    #             res.append(m)
    #     if self.results["warning"]:
    #         re.append("Compile errors:")
    #     return ("\n  - {}".format(res)).join(res)
    #     # return pformat(self.results)

    def validate_config(self, cfg=None):
        """
        Raises:
            ConfigurationError
        Returns:
            (int) Current file format version as defined in `file_version: stressor#N`
        """
        if cfg is None:
            cfg = self.run_config

        def _check_type(key, types):
            try:
                o = get_dict_attr(cfg, key)
            except Exception:
                self.report_error("Could not find expected entry", stack=key)
                return False
            if not isinstance(o, types):
                self.report_error(
                    "Expected type {}, but found {!r}".format(types, type(o)), stack=key
                )
                return False
            return True

        sections = set(cfg.keys())
        known_sections = set(("file_version", "run_config", "sequences"))

        file_version = cfg.get("file_version", "")
        if not file_version.startswith("stressor#"):
            raise ConfigurationError(
                "Not a `stressor` file (missing 'stressor#VERSION' tag)."
            )
        file_version = int(file_version.split("#", 1)[1])
        if file_version != self.FILE_VERSION:
            raise ConfigurationError(
                "File version mismatch: expected {}, but found {}.".format(
                    self.FILE_VERSION, file_version
                )
            )

        missing = known_sections.difference(sections)
        extra = sections.difference(known_sections)
        if extra or missing:
            raise ConfigurationError(
                "Configuration file check failed:\n  missing sections: {}\n  invalid sections: {}".format(
                    ", ".join(missing), ", ".join(extra)
                )
            )

        _check_type("run_config.context", (dict, None))
        _check_type("run_config.sessions", dict)

        #   - sequences must be a dict of dicts.
        #     All entries must contain 'activity'
        #   - activity.assert_json must be a dict
        sequence_names = set()
        if _check_type("sequences", dict):
            for seq_name, act_list in cfg["sequences"].items():
                sequence_names.add(seq_name)
                stack = "sequences/{}".format(seq_name)
                if not isinstance(act_list, list):
                    self.report_error(
                        "Expected list of activities", stack=stack,
                    )
                else:
                    for idx, act_def in enumerate(act_list):
                        stack = "sequences/{}#{:02}".format(seq_name, idx)
                        if not isinstance(act_def, dict):
                            self.report_error(
                                "Expected dict with `activity` key", stack=stack,
                            )
                        else:
                            activity = act_def.get("activity")
                            if not isinstance(activity, ActivityBase):
                                self.report_error(
                                    "`activity` must be an instance of ActivityBase "
                                    "instance (found {!r})".format(activity),
                                    stack=stack,
                                )
                            assert_match = act_def.get("assert_match")
                            if assert_match is not None:
                                try:
                                    re.compile(assert_match)
                                except re.error as e:
                                    self.report_error(
                                        "Invalid regular expression: {}: {}".format(
                                            assert_match, e
                                        ),
                                        stack=stack,
                                    )

        # Scenario list must contain 'sequence' keys and all sequences must exist
        if _check_type("run_config.scenario", list):
            for idx, seq_def in enumerate(cfg["run_config"]["scenario"]):
                stack = "run_config.scenario#{:02}".format(idx)
                if not isinstance(seq_def, dict) or "sequence" not in seq_def:
                    self.report_error(
                        "Expected dict with `sequence` key", stack=stack,
                    )
                elif seq_def["sequence"] not in sequence_names:
                    self.report_error(
                        "sequence name is not defined in `sequences`", stack=stack,
                    )

        # TODO:
        #   - if init is given, it must be first?
        #   - if end is given, it must be last?
        #   - assert_json, assert_match, ...
        return file_version

    def _compile(self, value, parent=None, parent_key=None, stack=None):
        """Apply load-time conversions after a config file was read.

        - Replace activity definitions with instances of :class:`ActvityBase`
        - Resolve load-time macros (partly by replacing them with activites)

        **Note:** Some makros, especially `$(CONTEXT.VAR)` are *not* resolved here,
        because this needs to be done at run-time.
        """
        stats = self.stats_manager
        if stack is None:
            self.stack = PathStack("config")
            stack = self.stack
            # Register sequence names
            for seq_name in value.get("sequences", {}).keys():
                stats.register_sequence(seq_name)

        with stack.enter(parent_key, ignore=parent is None):
            # logger.debug("compile {}".format(stack))

            # Resolve lists and dicts recursively:
            if isinstance(value, dict):
                # Macros may change the dictionary size, so iterate over a copy
                for key, sub_val in tuple(value.items()):
                    self._compile(sub_val, value, key, stack)
                return
            elif isinstance(value, (list, tuple)):
                # Macros may change the list size, so iterate over a copy
                for idx, elem in tuple(enumerate(value)):
                    self._compile(elem, value, idx, stack)
                return

            if isinstance(value, str) and "$" in value:
                has_match = False
                for macro_cls in macro_plugin_map.values():
                    try:
                        macro = macro_cls()
                        handled, res = macro.match_apply(self, parent, parent_key)
                        if handled:
                            has_match = True
                            logger.debug("Eval {}: {} => {}".format(stack, value, res))
                            # Re-init `value` in case the macro replaced it
                            value = parent[parent_key]
                            break
                    except Exception as e:
                        msg = "Could not evaluate macro {!r}".format(value)
                        self.report_error(msg, exc=e)
                        # raise ConfigurationError(
                        #     "Could not evaluate {!r} at {}: {}".format(value, stack, e)
                        # ) from e

                if not has_match and GENERIC_MACRO_REX.match(value):
                    msg = "Entry looks like a macro, but has no handler: '{}'".format(
                        value
                    )
                    self.report_error(msg, level="warning")

            # Either 'activity' was already an activity name, or a preceeding macro
            # set it:
            if isinstance(value, str) and value in activity_plugin_map:
                # Replace the activity definition with an instance of the class.
                #
                # Allow activities to do compile-time checking ad processing
                # static_activity_key =
                activity_cls = activity_plugin_map[value]
                try:
                    # print(parent)
                    activity_inst = activity_cls(self, **parent)
                    parent[parent_key] = activity_inst
                    if stats:
                        stats.register_activity(activity_inst)
                except Exception as e:
                    msg = "Could not evaluate activity {!r}".format(value)
                    self.report_error(msg, exc=e)
                    # logger.error("{} {}: {}".format(stack, value, e))

        return

    def read(self, path, load_files=True):
        """Read a YAML file into ``self.config_all``.

        Raises:
            ConfigurationError
        """
        check_arg(load_files, bool)

        self.config_all = None

        if not path.lower().endswith(".yaml"):
            path += ".yaml"
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise ConfigurationError("File not found: {}".format(path))
        self.path = path
        self.root_folder = os.path.dirname(path)
        self.name = os.path.splitext(os.path.basename(path))[0]

        with open(path, "rt") as f:
            try:
                res = yaml.safe_load(f)
            except yaml.parser.ParserError as e:
                raise ConfigurationError("Could not parse YAML: {}".format(e)) from None

        self._compile(res)

        self.file_version = self.validate_config(res)

        if self.results["warning"]:
            logger.error("Compiler warnings:")
            for m in self.results["warning"]:
                logger.warning("  - {}: {}".format(m["path"], m["msg"]))

        if self.results["error"]:
            logger.error("Compiler errors:")
            for m in self.results["error"]:
                logger.error("  - {}: {}".format(m["path"], m["msg"]))
            raise ConfigurationError("Config file had compile errors.")

        self.config_all = res
        # self.run_config = res["run_config"]
        # self.context = self.run_config["context"]
        # self.sequences = res["sequences"]
        return self.config_all
