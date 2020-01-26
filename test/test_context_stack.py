# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""

import os

import pytest

from stressor.context_stack import ContextStack  # , RunContext


# class TestRunContext:
# def test_1(self):
#     ctx = RunContext(None, "test", {})
#     assert ctx


class TestContextStack:
    def setup_method(self):
        self.fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        self.context_stack = ContextStack()

    def teardown_method(self):
        pass

    def test_1(self):
        cm = self.context_stack
        with pytest.raises(IndexError):
            cm.peek()

        assert cm.path() == "/"

        cm.push("t1", {"root": "http://example.com", "url": "page_1"}, copy_data=True)
        assert cm.peek().name == "t1"
        assert cm.path() == "/t1"
        assert cm.as_dict() == {
            "root": "http://example.com",
            "url": "page_1",
        }

        cm.push("t2", {"url": "page_2"}, copy_data=True)
        assert cm.path() == "/t1/t2"
        assert cm.as_dict() == {
            "root": "http://example.com",
            "url": "page_2",
        }

        assert cm.peek().name == "t2"
        assert cm.pop().name == "t2"
        assert cm.peek().name == "t1"
        assert cm.path() == "/t1"
        assert cm.as_dict() == {
            "root": "http://example.com",
            "url": "page_1",
        }

        assert cm.pop().name == "t1"
        with pytest.raises(IndexError):
            cm.pop()
        with pytest.raises(IndexError):
            cm.peek()

        with pytest.raises(RuntimeError):
            for i in range(ContextStack.MAX_DEPTH + 1):
                cm.push("t{}".format(i), {})
