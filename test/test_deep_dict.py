# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""

import pytest

from stressor.deep_dict import DeepDict, get_dict_attr


class TestDeepDict:
    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_get_attr(self):
        d = {
            "s1": 1,
            "s2": "foo",
            "l1": [],
            "l2": [1, 2, 3],
            "d1": {},
            "d2": {"d21": 42, "d22": {"d221": "bar"}},
        }
        assert get_dict_attr(d, "s1") == 1
        assert get_dict_attr(d, "l1") == []
        assert get_dict_attr(d, "l2") == [1, 2, 3]
        assert get_dict_attr(d, "l2.[1]") == 2
        assert get_dict_attr(d, "d1") == {}
        assert get_dict_attr(d, "d2.d21") == 42
        assert get_dict_attr(d, "d2.d22.d221") == "bar"

        with pytest.raises(KeyError):
            get_dict_attr(d, "foobar")
        with pytest.raises(ValueError, match=r".*cannot be nested.*"):
            get_dict_attr(d, "s1.foobar")
        with pytest.raises(ValueError, match=r".*Use `\[INT\]` syntax.*"):
            get_dict_attr(d, "l2.foobar")
        with pytest.raises(IndexError):
            get_dict_attr(d, "l2.[99]")
        with pytest.raises(KeyError):
            get_dict_attr(d, "d1.foobar")

    def test_1(self):
        dd = DeepDict({})

        assert dd == dd
