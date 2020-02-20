# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import logging
import os
import sys
import warnings

try:
    import sty
except SyntaxError:
    # sty reuqires Python >= 3.6
    sty = None


logger = logging.getLogger("stressor")


class Log:
    """
    """

    _initialized = False

    def __init__(self, logger_name, enable_color=False):
        self.logger_name = logger_name
        self.enable_color(enable_color)

    def _initialize(self):
        if self._initialized:
            return
        # Shim to make colors work on Windows
        if sys.platform == "win32":
            os.system("color")
        self._initialized = True

    def enable_color(self, flag):
        if flag and sty is None:
            warnings.warn("Colored output requires Python 3.6+")
            flag = False
        if flag:
            self._initialize()
        self.use_colors = flag

    def color(self, msg, fg, bg=None, bold=False, underline=False, italic=False):
        if self.use_colors:
            sl = []
            if fg:
                sl.append(getattr(sty.fg, fg))
            if bg:
                sl.append(getattr(sty.bg, bg))
            if bold:
                sl.append(sty.ef.bold)
            if underline:
                sl.append(sty.ef.underl)
            if italic:
                sl.append(sty.ef.italic)
            sl.append(msg)
            # if bold or underline or italic:
            #     sl.append(sty.ef.rs)
            if bg:
                sl.append(sty.bg.rs)
            if fg:
                sl.append(sty.fg.rs)
            msg = "".join(str(s) for s in sl)
        return msg

    def red(self, msg):
        return self.color(msg, "li_red")

    def yellow(self, msg):
        return self.color(msg, "yellow")

    def green(self, msg):
        return self.color(msg, "green")


log = Log("stressor", False)


def red(msg):
    return log.color(msg, "li_red")


def yellow(msg):
    return log.color(msg, "yellow")


def green(msg):
    return log.color(msg, "green")
