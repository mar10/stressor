# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from copy import deepcopy

from stressor.util import check_arg, get_dict_attr


class RunContext:
    """Basically a dict, holding context variables as key/value pairs.

    The :class:`ContextStack` organizes instances of this class as stack,
    so we can have a scope-dependant context.

    Values may contain `$...` macros.

    Attributes:
        parent (:class:`RunContext`):
            The stack frame parent or None if this is the root.
        name (str):
            A short name for this context. The context manager uses it to concatenate
            a path string for the current scope.
        own_attributes (dict):
            A dict of attributes that are explicitly defined by this instance.
        all_attributes (dict):
            The aggregated context, created by overloading the parent's context
            with our own ``attributes``
    """

    def __init__(self, parent, name, update_attributes=None, copy_data=False):
        """
        Args:
            parent (:class:`RunContext`):
                The stack frame parent or None if this is the root.
            name (str):
                A short name for this context. The context manager uses it to concatenate
                a path string for the current scope.
            update_attributes (dict):
                A dict of attributes that are explicitly defined by this instance.
            copy_data (bool):

        """
        check_arg(parent, RunContext, or_none=True)
        check_arg(name, str, name != "")
        check_arg(update_attributes, dict, or_none=True)
        check_arg(copy_data, bool)

        self.parent = parent
        self.name = name
        if update_attributes is None:
            self.own_attributes = {}
        else:
            self.own_attributes = deepcopy(update_attributes)

        if parent is None:
            self.all_attributes = self.own_attributes
        elif copy_data:
            # Create a copy of the parent's context, so the original state is
            # restored on pull
            self.all_attributes = deepcopy(parent.all_attributes)
            if self.own_attributes:
                self.all_attributes.update(self.own_attributes)
        else:
            # We only reference the parent context instance, so change will persist
            # after a popping from this stack
            self.all_attributes = parent.all_attributes

        return


class ContextStack:
    """
    The context manager
    Examples:
    """

    MAX_DEPTH = 100

    def __init__(self, name=None, context=None):
        self.ctx_stack = []
        if context is not None:
            assert name
            rc = RunContext(None, name or "root", context)
            self._push(rc)

    def __str__(self):
        return self.path()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pop()
        return

    @property
    def context(self):
        ctx = self.ctx_stack[-1].all_attributes
        return ctx

    def enter(self, name, attributes=None):
        self.push(name, attributes)
        return self

    def level(self):
        return len(self.ctx_stack)

    def _push(self, context):
        """
        Raises:
            RuntimeError if queue length exceeds ContextStack.MAX_DEPTH
        """
        check_arg(context, RunContext)

        if len(self.ctx_stack) >= self.MAX_DEPTH:
            raise RuntimeError("Max depth exceeded ({})".format(self.MAX_DEPTH))
        self.ctx_stack.append(context)
        return context

    def push(self, name, attributes=None, copy_data=False):
        """Push `name` to the stack and optionally update or copy context.
        Args:
            name (str):
        Raises:
            RuntimeError if queue length exceeds ContextStack.MAX_DEPTH
        """
        check_arg(name, str)
        check_arg(attributes, dict, or_none=True)

        try:
            parent = self.peek()
        except IndexError:
            parent = None

        ctx = RunContext(parent, name, attributes, copy_data)
        return self._push(ctx)

    def pop(self):
        """
        Raises:
            IndexError if queue is empty
        """
        ctx = self.ctx_stack.pop()
        return ctx

    def peek(self, offset=1):
        """
        Raises:
            IndexError if offset is invalid
        """
        assert offset > 0
        ctx = self.ctx_stack[-offset]
        return ctx

    def path(self):
        path = "/".join((ctx.name for ctx in self.ctx_stack))
        return "/" + path

    def as_dict(self):
        """Return the current aggregated context."""
        return self.context

    def get_attr(self, key_path, context=None):
        check_arg(key_path, str)
        check_arg(context, RunContext, or_none=True)
        if context is None:
            context = self.peek()
        return get_dict_attr(self.as_dict(), key_path)

    def set_last_part(self, name):
        self.ctx_stack[-1].name = name
