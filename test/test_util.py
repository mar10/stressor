# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import pytest

from stressor.util import (
    assert_always,
    PathStack,
    check_arg,
    shorten_string,
    format_elap,
)


class TestBasics:
    def test_assert(self):
        assert_always(1)
        assert_always(1, "test")
        with pytest.raises(AssertionError):
            assert_always(0)
        with pytest.raises(AssertionError, match=".*foobar.*"):
            assert_always(0, "foobar")

    def test_check_arg(self):
        def foo(name, amount, options=None):
            check_arg(name, str)
            check_arg(amount, (int, float), amount > 0)
            check_arg(options, dict, or_none=True)
            return name

        assert foo("x", 10) == "x"
        assert foo("x", 10, {1: 2}) == "x"
        with pytest.raises(TypeError, match=".*but got <class 'int'>.*"):
            foo("x", 10, 42)
        with pytest.raises(ValueError, match=".*Invalid argument value.*"):
            foo("x", -10)
        return

    def test_pathstack(self):
        path = PathStack()
        assert str(path) == "/"
        path.push("root")
        assert str(path) == "/root"
        with path.enter("sub1"):
            assert str(path) == "/root/sub1"
        assert str(path) == "/root"
        assert path.pop() == "root"
        with pytest.raises(IndexError):
            path.pop()

    def test_shorten_string(self):
        s = (
            "Do you see any Teletubbies in here?"
            "Do you see a slender plastic tag clipped to my shirt with my name printed on it?"
        )
        assert shorten_string(None, 10) is None
        assert len(shorten_string(s, 20)) == 20
        assert len(shorten_string(s, 20, min_tail_chars=7)) == 20
        assert shorten_string(s, 20) == "Do you see any [...]"
        assert shorten_string(s, 20, min_tail_chars=7) == "Do you s[...] on it?"

    def test_format_elap(self):
        assert format_elap(1.23456) == "1.2 sec"
        assert format_elap(1.23456, high_prec=True) == "1.235 sec"
        assert format_elap(3677) == "1:01:17 hrs"
        assert format_elap(12.34, count=10) == "12.3 sec, 0.8 items/sec"
