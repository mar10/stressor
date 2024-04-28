# (c) 2020-2024 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

import pytest

from stressor.config_manager import (
    ConfigManager,
    ConfigurationError,
    replace_var_macros,
)
from stressor.plugin_manager import PluginManager
from stressor.statistic_manager import StatisticManager


class TestConfigReader:
    def setup_method(self):
        self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        PluginManager.register_plugins(arg_parser=None)

    def test_path_check(self):
        path = os.path.join(self.fixtures_path, "INVALID")
        stats = StatisticManager()
        cr = ConfigManager(stats)
        with pytest.raises(ConfigurationError, match=r".*not found.*"):
            cr.read(path)

    def test_replace_var_macros(self):
        context = {
            "root_url": "http://example.com/$(mountpoint)",
            "mountpoint": "s1",
            "guid": "42",
            "user": {"name": "joe", "password": "secret"},
        }
        value = {
            "a": "$(root_url)?guid=$(guid)",
            "b": "$(root_url)?user=$(user.name)",
        }
        replace_var_macros(value, context)
        assert value["a"] == "http://example.com/s1?guid=42"
        assert value["b"] == "http://example.com/s1?user=joe"

    def test_read_scenario(self):
        path = os.path.join(self.fixtures_path, "test_dry_run")
        stats = StatisticManager()
        cm = ConfigManager(stats)
        res = cm.read(path)
        assert res is cm.config_all
        assert cm.root_folder == self.fixtures_path

        # Check load time macros
        assert cm.sessions["users"][0] == {
            "name": "User_1",
            "password": "secret",
            "custom": "foo",
        }, "$load() macro"

        # SleepActivity
        activity_dict = cm.sequences["init"][1]
        assert activity_dict["activity"].__class__.__name__ == "SleepActivity"
        assert activity_dict["duration"] == 0.01

        # $sleep(.01):
        activity_dict = cm.sequences["init"][2]
        assert activity_dict["activity"].__class__.__name__ == "SleepActivity"
        assert activity_dict["duration"] == 0.02

        # $sleep($(default_sleep))
        activity_dict = cm.sequences["init"][3]
        assert activity_dict["activity"].__class__.__name__ == "SleepActivity"
        assert activity_dict["duration"] == "$(default_sleep)"

        # $sleep(0.01, .02):
        activity_dict = cm.sequences["init"][4]
        assert activity_dict["activity"].__class__.__name__ == "SleepActivity"
        assert activity_dict["duration"] == 0.01
        assert activity_dict["duration_2"] == 0.02

        return

    # def test_read_scenario_2(self):
    #     path = os.path.join(self.fixtures_path, "test_mock_server")
    #     cr = ConfigManager(None)
    #     res = cr.read(path)
    #     assert res is cr.config_all
    #     assert cr.root_folder == self.fixtures_path
    #     # Check load time macros
    #     assert cr.run_config["sessions"]["users"][0] == {
    #         "name": "User_1",
    #         "password": "secret",
    #     }, "$load() macro"

    #     activity_dict = cr.sequences["init"][2]
    #     assert activity_dict["activity"].__class__.__name__ == "SleepActivity"
    #     assert activity_dict["duration"] == ".1"

    #     return
