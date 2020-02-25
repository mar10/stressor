# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""

import os

# import pytest

from stressor.convert.har_converter import HarConverter


class TestConvert:
    def setup_method(self):
        self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")

    def teardown_method(self):
        pass

    def test_1(self):
        path = os.path.join(self.fixtures_path, "har_1.har")
        conv = HarConverter()
        conv.parse(path)
        assert len(conv.entries) == 5
        assert conv.version == "1.2"
        # assert 0
