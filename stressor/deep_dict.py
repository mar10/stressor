# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
# from copy import deepcopy

from stressor.util import check_arg


def get_dict_attr(d, key_path):
    """Return the value of a nested dict using dot-notation path.

    Args:
        d (dict):
        key_path (str):
    Raises:
        KeyError:
        ValueError:
        IndexError:

    Examples::

        ...

    Todo:
        * k[1] instead of k.[1]
        * default arg
    """
    check_arg(d, dict)

    seg_list = key_path.split(".")
    value = d[seg_list[0]]
    for seg in seg_list[1:]:
        if isinstance(value, dict):
            value = value[seg]
        elif isinstance(value, (list, tuple)):
            if not seg.startswith("[") or not seg.endswith("]"):
                raise ValueError("Use `[INT]` syntax to address list items")
            seg = seg[1:-1]
            value = value[int(seg)]
        else:
            raise ValueError("Segment '{}' cannot be nested".format(seg))

    return value


class DeepDict(dict):
    """
    A - potentially nested - dict, with support for macro expansion and
    access using dot-notation paths.

    The :class:`RunContext` organizes instances of this class as stack,
    so we can have a scope-dependant context.

    Values may contain `$...` macros.
    """

    def __init__(self, source):
        super()
        self.copy_deep = True

    # def __get__(self, key):
    #     if "." not in key:
    #         return super().__get__(key)
    #     raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def get(self, path, context=None):
        if "." not in path:
            return super()
        raise NotImplementedError
