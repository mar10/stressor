# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

from stressor.run_manager import RunManager


class TestRunManager:
    def setup_method(self):
        self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")

    def test_dry_run(self):
        config_path = os.path.join(self.fixtures_path, "test_dry_run.yaml")
        rm = RunManager()

        activities = []
        errors = []

        def notify_hook(channel, *args, **kwargs):
            if channel == "end_activity":
                activities.append(
                    "{} {}".format(kwargs.get("path"), kwargs.get("activity_args"))
                )
                print(
                    "EXECUTE {} {}".format(
                        kwargs.get("path"), kwargs.get("activity_args")
                    )
                )
                # activities.append("{} {}".format(kwargs.get("path"), kwargs["activity"]))
            if kwargs.get("error"):
                errors.append("{} {error}".format(channel, **kwargs))

            # print("notify_hook({})".format(channel), args, kwargs)
            # print("notify_hook({})".format(channel), kwargs.get("path"), kwargs.get("elap"))

        rm.subscribe("*", notify_hook)
        rm.load_config(config_path)
        assert rm.run_config
        assert rm.config_manager.file_version == 0
        # assert rm.c"extra_opt".file_version == 0
        # assert "GetRequest" in activity_plugin_map

        options = {}
        extra_config = {
            "extra_opt": "extra_val",
            "dry_run": True,
        }
        res = rm.run(options, extra_config)
        assert res is True
        assert errors == []
        # assert activities == []
        # assert 0

    def test_mock_server(self, mock_wsgidav_server_fixture):
        config_path = os.path.join(self.fixtures_path, "test_mock_server.yaml")
        rm = RunManager()
        rm.load_config(config_path)
        assert rm.run_config
        assert rm.config_manager.file_version == 0
        options = {}
        extra_config = {}
        res = rm.run(options, extra_config)
        assert res is True
        # assert 0
