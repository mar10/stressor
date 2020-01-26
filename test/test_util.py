# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import pytest

from stressor.util import assert_always, PathStack, check_arg


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
