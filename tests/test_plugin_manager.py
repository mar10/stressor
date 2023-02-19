# -*- coding: utf-8 -*-
# (c) 2020-2023 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from stressor.plugin_manager import PluginManager


class TestPluginManager:
    # def setup_method(self):
    #     self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")

    def test_plugins(self):
        pm = PluginManager
        pm.register_plugins(arg_parser=None)
        assert "PsAlloc" in pm.activity_plugin_map
