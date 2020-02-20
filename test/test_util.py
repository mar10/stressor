# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import sys

import pytest

from stressor.util import (
    PathStack,
    assert_always,
    check_arg,
    format_elap,
    get_dict_attr,
    parse_args_from_str,
    shorten_string,
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

    def test_get_attr(self):

        # next_
        class TestClass:  # noqa: B903
            def __init__(self, val):
                self.val = val

        d = {
            "s1": 1,
            "s2": "foo",
            "l1": [],
            "l2": [1, 2, 3],
            "d1": {},
            "d2": {"d21": 42, "d22": {"d221": "bar"}},
            "o": TestClass("baz"),
        }
        assert get_dict_attr(d, "s1") == 1
        assert get_dict_attr(d, "l1") == []
        assert get_dict_attr(d, "l2") == [1, 2, 3]
        assert get_dict_attr(d, "l2.[1]") == 2
        assert get_dict_attr(d, "d1") == {}
        assert get_dict_attr(d, "d2.d21") == 42
        assert get_dict_attr(d, "d2.d22.d221") == "bar"
        assert get_dict_attr(d, "o.val") == "baz"

        with pytest.raises(KeyError):
            get_dict_attr(d, "foobar")
        with pytest.raises(
            AttributeError, match=r".*object has no attribute 'foobar'.*"
        ):
            get_dict_attr(d, "s1.foobar")
        with pytest.raises(ValueError, match=r".*Use `\[INT\]` syntax.*"):
            get_dict_attr(d, "l2.foobar")
        with pytest.raises(IndexError):
            get_dict_attr(d, "l2.[99]")
        with pytest.raises(KeyError):
            get_dict_attr(d, "d1.foobar")

        # Defaults:
        assert get_dict_attr(d, "foobar", "def") == "def"
        assert get_dict_attr(d, "s1.foobar", "def") == "def"
        assert get_dict_attr(d, "l2.foobar", "def") == "def"
        assert get_dict_attr(d, "l2.[99]", "def") == "def"
        assert get_dict_attr(d, "foobar", "def") == "def"
        assert get_dict_attr(d, "d1.foobar", "def") == "def"

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
        assert format_elap(1.23456) == "1.23 sec"
        assert format_elap(1.23456, high_prec=True) == "1.235 sec"
        assert format_elap(3677) == "1:01:17 hrs"
        assert format_elap(367) == "6:07 min"
        assert format_elap(367, high_prec=True) == "6:07.00 min"
        assert format_elap(12.34, count=10) == "12.3 sec, 0.8 items/sec"

    def test_parse_args_from_str(self):
        arg_def = (
            ("min", float),
            ("max", float, None),
        )
        res = parse_args_from_str("1.23", arg_def)
        assert res == {"min": 1.23, "max": None}

        res = parse_args_from_str("1.23, 42", arg_def)
        assert res == {"min": 1.23, "max": 42.0}

        with pytest.raises(TypeError):
            parse_args_from_str(None, arg_def)

        with pytest.raises(ValueError, match=".*Extra arg.*"):
            parse_args_from_str("1.23, 42, 32", arg_def)

        with pytest.raises(ValueError, match=".*convert string to float: 'foo'.*"):
            parse_args_from_str("1.23, foo", arg_def)

        arg_def = (
            ("min", float, 1.0),
            ("max", float, None),
        )
        res = parse_args_from_str("1.23", arg_def)
        assert res == {"min": 1.23, "max": None}

        res = parse_args_from_str("", arg_def)
        assert res == {"min": 1.0, "max": None}, "'$name()' uses default args"

        arg_def = (
            ("name", str),
            ("hint", str, "test"),
        )
        res = parse_args_from_str("foo", arg_def)
        assert res == {"name": "foo", "hint": "test"}

        res = parse_args_from_str("", arg_def)
        assert res == {"name": "", "hint": "test"}

        res = parse_args_from_str(",", arg_def)
        assert res == {"name": "", "hint": ""}

        # Allow single and double quotes
        res = parse_args_from_str("'foo', ' bar '", arg_def)
        assert res == {"name": "foo", "hint": " bar "}

        res = parse_args_from_str('"foo", " bar "', arg_def)
        assert res == {"name": "foo", "hint": " bar "}

        arg_def = (
            ("name", str),
            ("amount", float),
            ("hint", str, "test"),
        )
        with pytest.raises(ValueError, match="Missing mandatory arg `amount.*"):
            parse_args_from_str("1.23", arg_def)

        # Allow $() macros
        arg_def = (("amount", float),)
        res = parse_args_from_str("$(def_amount)", arg_def)
        assert res == {"amount": "$(def_amount)"}

        # # Parse `$(context_key)` macros
        # ctx = {"base_url": "http://example.com", "def_amount": 7}
        # res = parse_args_from_str("$(base_url)/foo, $(def_amount)", arg_def, ctx)
        # assert res == {"name": "http://example.com/foo", "amount": 8, "hint": "test"}

    def test_log(self):
        from stressor.log import Log

        log = Log("stressor", False)
        assert log.red("error") == "error"
        assert log.green("ok") == "ok"

        log = Log("stressor", True)
        if sys.version_info < (3, 6):
            assert log.red("error") == "error", "Python 3.5 must disable colors"
            assert log.green("ok") == "ok"
        else:
            assert log.red("error") == "\x1b[91merror\x1b[39m"
            assert log.green("ok") == "\x1b[32mok\x1b[39m"
