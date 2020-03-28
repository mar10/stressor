# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""

import os
import tempfile

import pytest

from stressor.convert.har_converter import HarConverter


class TestConvert:
    def setup_method(self):
        self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")

    def teardown_method(self):
        pass

    def test_1(self):
        with tempfile.TemporaryDirectory() as target_folder:
            opts = {
                "fspec": os.path.join(self.fixtures_path, "har_1.har"),
                "target_folder": target_folder,
                "collate_max_len": 0,
            }
            conv = HarConverter(opts)
            conv.run()
            act_yaml_path = os.path.join(target_folder, "main_sequence.yaml")
            yaml = open(act_yaml_path, "rt").read()
            # print(yaml)
            assert len(conv.entries) == 5
            assert conv.har_version == "1.2"
        assert "activity: GetRequest" in yaml
        assert 'url: "/test1.json"' in yaml
        # assert 'url: "http://127.0.0.1:8082/test1.json"' in yaml
        # assert 0

    def test_2(self):
        # This test is only useful to inspect the folder while developing
        # TODO: remove later
        target_folder = "/Users/martin/temp"
        if not os.path.isdir(target_folder):
            pytest.skip("Local test folder not found")
        opts = {
            "fspec": os.path.join(self.fixtures_path, "har_2.har"),
            "target_folder": target_folder,
            "force": True,
        }
        conv = HarConverter(opts)
        conv.run()
        # yaml = open(opts["fspec"], "rt").read()
        # print(yaml)
        assert len(conv.entries) == 27  # 47
        assert conv.stats["entries"] == 27
        assert conv.stats["entries_total"] == 51
        assert conv.stats["external_urls"] == 4
        assert conv.stats["skipped"] == 24
        assert conv.stats["collated_activities"] == 10
        assert conv.stats["collated_urls"] == 33

        assert conv.har_version == "1.2"
        # assert 0
