# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re
from abc import ABC, abstractmethod

from stressor.util import StressorError, assert_always, check_arg, logger

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


def register_plugins():
    register_activity_plugins()
    register_macro_plugins()


class ActivityError(StressorError):
    """Base for all errors that are explicitly raised by activities."""


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

    #: Name by which the actvity can be used in YAML configurations.
    #: Defaults to class name without trailing `...Activity`, e.g.
    #: 'SleepActivity' is called as ``activity: Sleep``
    _script_name = None

    #: If defined, the default implementation of `compile()` will raise an error
    #: if any of those args is not defined
    _mandatory_args = None

    # #: (bool)
    # _default_monitor = False

    #: (bool)
    _default_ignore_timing = False

    @classmethod
    def get_script_name(cls):
        # Note: we must check `cls.__dict__` instead of `cls._script_name`,
        # because we want to test the local class attribute (not a derived one):
        if cls.__dict__.get("_script_name") is None:
            assert_always(cls.__name__.endswith("Activity"))
            cls._script_name = cls.__name__[:-8]
        return cls._script_name

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
            compile_path (str):
            raw_args (dict):
        Args:
            compile_path (:class:`PathStack`):
                The location breadcrumb path of this activity in the configration
                structure, e.g. 'main/#4'.
            activity_args (dict):
                named arguments that were passed to the activity definition.
                Note that the arguments are read at load-time and are not yet
                expanded (i.e. may contain `$(context_var)` macros).
        """
        self.compile_path = str(config_manager.stack)
        self.raw_args = activity_args

    def __str__(self):
        """Return a descriptive string."""
        return self.get_info()

    def get_info(self, expanded_args=None):
        """Return a descriptive string (optionally using expanded args)."""
        args = self.raw_args if expanded_args is None else expanded_args
        args = ("{}: {!r}".format(*kv) for kv in args.items())
        return "{}({})".format(self.get_script_name(), ", ".join(args))

    @abstractmethod
    def execute(self, session, **expanded_args):
        """
        Called by the :class:`SessionManager`, directly after __init__.

        The constructor is called by the :class:`SessionManager`, after
        `$(context.var)` macros have been resolved if any.

        The defaulat implementation stores `activity_args` as `self.raw_args`,
        however derived classes may choose to add named args explicitly for
        better readability and checking.
        A derived class MUST implement this method and

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
        """Parse current value and call self.apply() if thw macro matches.

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
        res = self.apply(context_reader, parent, parent_key, *args)
        # logger.debug("Eval {}: {} => {}".format(stack, value, res))
        return (True, res)

    @abstractmethod
    def apply(self, context_reader, parent, parent_key, *args):
        """
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
