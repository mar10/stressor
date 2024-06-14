# (c) 2020-2024 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pkg_resources import iter_entry_points

from stressor.plugins.base import ActivityBase, MacroBase
from stressor.util import logger


class PluginManager:
    """
    Load, cache, and maintain a list of plugins and workflow tasks.

    This is basically a singleton.
    """

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

    #: (str) Entry point group name
    namespace = "stressor.plugins"
    #: (bool) True when all plugin entry points are loaded
    entry_points_searched = False
    #: (bool) True when all plugins' 'register()' method were called.
    plugins_registered = False
    #: (dict) Cached map TASK_NAME => EntryPoint of loaded entry_points
    _entry_point_map = {}

    def __init__(self):
        pass

    @classmethod
    def find_plugins(cls):
        """Load all entry points with group name 'stressor.plugins'."""
        if cls.entry_points_searched:
            return
        cls.entry_points_searched = True
        ep_map = cls._entry_point_map
        logger.debug(f"Search entry points for group '{cls.namespace}'...")

        for ep in iter_entry_points(group=cls.namespace, name=None):
            plugin_name = f"{ep.dist}"
            logger.debug(f"Found plugin {plugin_name} from entry point `{ep}`")

            if ep.name in ep_map:
                logger.warning(f"Duplicate entry point name: {ep.name}; skipping...")
                continue
            # elif ep.name in cls.task_class_map:
            #     # TODO: support overriding standard tasks?
            #     # Maybe when 'extras=[override]' is passed...
            #     logger.warning(
            #         "Plugin task name already exists: {}; skipping...".format(ep.name)
            #     )
            #     continue

            ep_map[ep.name] = ep

        return

    @classmethod
    def _register_subclasses(cls, base_cls, cls_map):
        """Register currently loaded plugins.

        These are all currently known subclasses of
        :class:`stressor.plugins.base.ActivityBase` and
        :class:`stressor.plugins.base.MacroBase` .
        """
        for sub_cls in base_cls.__subclasses__():
            name = sub_cls.get_script_name()
            existing_cls = cls_map.get(name)
            if existing_cls is sub_cls:
                continue  # already registered
            elif existing_cls is None:
                if not name.startswith("_"):
                    cls_map[name] = sub_cls
                cls._register_subclasses(sub_cls, cls_map)
            else:
                raise RuntimeError(f"Class name conflict: {sub_cls}")
        return

    @classmethod
    def register_plugins(cls, arg_parser):
        """Call `register_fn` on all loaded entry points."""
        if cls.plugins_registered:
            return
        cls.plugins_registered = True

        # Import stock class definitions, so we can scan the subclasses.
        # This will add standard plugins to ActivityBase.__subclasses__()
        # and MacroBase.__subclasses__():
        import stressor.plugins.common  # noqa F401
        import stressor.plugins.http_activities  # noqa F401
        import stressor.plugins.report_activities  # noqa F401
        import stressor.plugins.script_activities  # noqa F401

        # Load entry points from all installed mosules that have the
        # 'stressor.plugins' namespace:
        cls.find_plugins()

        # Call `register_fn` on all loaded entry points_
        ep_map = cls._entry_point_map
        for name, ep in cls._entry_point_map.items():
            logger.info(f"Load plugins {ep.dist}...")
            try:
                register_fn = ep.load()
                if not callable(register_fn):
                    raise RuntimeError(f"Entry point {ep} is not a function")
                ep_map[ep.name] = register_fn
            except Exception:
                logger.exception(f"Failed to load {ep}")

            prev_activities = list(ActivityBase.__subclasses__())
            prev_macros = list(MacroBase.__subclasses__())

            logger.debug(f"Register plugins {ep.dist}...")
            try:
                # The plugin must declare new classes derrived from
                # ActivityBase and/or MacroBase
                register_fn(
                    activity_base=ActivityBase,
                    macro_base=MacroBase,
                    arg_parser=arg_parser,
                )
            except Exception:
                logger.exception(f"Could not register {name}")
                continue

            found_one = False
            for activity_cls in ActivityBase.__subclasses__():
                if activity_cls in prev_activities:
                    continue
                found_one = True
                logger.info(f"Register {ep.dist}.{activity_cls}")

            for macro_cls in MacroBase.__subclasses__():
                if macro_cls in prev_macros:
                    continue
                found_one = True
                logger.info(f"Register {ep.dist}.{macro_cls}")

            if not found_one:
                logger.warning(
                    f"Plugin {ep.dist} did not register activites nor macros"
                )

        # Build plugin maps from currently known subclasses
        cls._register_subclasses(ActivityBase, cls.activity_plugin_map)
        logger.debug(f"Registered activity plugins:\n{cls.activity_plugin_map}")

        cls._register_subclasses(MacroBase, cls.macro_plugin_map)
        logger.debug(f"Registered macro plugins:\n{cls.macro_plugin_map}")
        return
