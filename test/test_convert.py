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
        fspec = os.path.join(self.fixtures_path, "har_1.har")
        conv = HarConverter()
        with tempfile.TemporaryDirectory() as target_folder:
            conv.run(fspec, target_folder)
            assert len(conv.entries) == 5
            assert conv.version == "1.2"
            act_yaml_path = os.path.join(target_folder, "main_activities.yaml")
            yaml = open(act_yaml_path, "rt").read()
            assert "activity: GetRequest" in yaml
            assert 'url: "http://127.0.0.1:8082/test1.json"' in yaml
        # assert 0

    def test_2(self):
        # This test is only useful to inspect the folder while developing
        # TODO: remove later
        target_folder = "/Users/martin/temp"
        if not os.path.isdir(target_folder):
            pytest.skip("Local test folder not found")
        fspec = os.path.join(self.fixtures_path, "har_1.har")
        conv = HarConverter()
        conv.run(fspec, target_folder)
        assert len(conv.entries) == 5
        assert conv.version == "1.2"
        # assert 0
