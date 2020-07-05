# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stylish
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Simple helper for colored terminal output.

Examples:
    from stylish import colored as _c

    if not args.no_color and sys.stdout.isatty():
        enable_colors(True)

"""
import os
import sys

# Foreground ANSI codes using SGR format:
_SGR_FG_COLOR_MAP = {
    "reset_all": 0,
    "reset_fg": 39,
    # These are well supported.
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    # These are less good supported.
    "li_black": 90,
    "li_red": 91,
    "li_green": 92,
    "li_yellow": 93,
    "li_blue": 94,
    "li_magenta": 95,
    "li_cyan": 96,
    "li_white": 97,
}

FG_MAP = {color: "\033[{}m".format(num) for color, num in _SGR_FG_COLOR_MAP.items()}

# Background ANSI codes using SGR format:
_SGR_BG_COLOR_MAP = {
    "reset_bg": 49,
    # These are well supported.
    "black": 40,
    "red": 41,
    "green": 42,
    "yellow": 43,
    "blue": 44,
    "magenta": 45,
    "cyan": 46,
    "white": 47,
    # These are less good supported.
    "li_black": 100,
    "li_red": 101,
    "li_green": 102,
    "li_yellow": 103,
    "li_blue": 104,
    "li_magenta": 105,
    "li_cyan": 106,
    "li_white": 107,
}

BG_MAP = {color: "\033[{}m".format(num) for color, num in _SGR_BG_COLOR_MAP.items()}

# ANSI codes using 8-bit format (used for fore- and background)

_BIT_COLOR_MAP = {
    # These are less supported.
    "da_black": 0,
    "da_red": 88,
    "da_green": 22,
    "da_yellow": 58,
    "da_blue": 18,
    "da_magenta": 89,
    "da_cyan": 23,
    "da_white": 249,
}

FG_MAP.update(
    {color: "\033[38;5;{}m".format(num) for color, num in _BIT_COLOR_MAP.items()}
)
BG_MAP.update(
    {color: "\033[48;5;{}m".format(num) for color, num in _BIT_COLOR_MAP.items()}
)


_SGR_EFFECT__MAP = {
    # Reset distinct effects
    "reset_all": 0,
    "reset_fg": 39,
    "reset_bg": 49,
    "reset_bold_dim": 22,
    "reset_dim_bold": 22,
    "reset_i": 23,
    "reset_italic": 23,
    "reset_u": 24,
    "reset_underline": 24,
    "reset_blink": 25,
    "reset_inverse": 27,
    "reset_hidden": 28,
    "reset_strike": 29,
    # Effects
    "b": 1,
    "bold": 1,
    "dim": 2,
    "i": 3,
    "italic": 3,
    "u": 4,
    "underline": 4,
    "blink": 5,
    "inverse": 7,
    "hidden": 8,
    "strike": 9,
}
EFFECT_MAP = {color: "\033[{}m".format(num) for color, num in _SGR_EFFECT__MAP.items()}


def rgb_fg(r, g, b):
    return "\x1b[38;2;{};{};{}m".format(r, g, b)


def rgb_bg(r, g, b):
    return "\x1b[48;2;{};{};{}m".format(r, g, b)


# In 2016, Microsoft released the Windows 10 Version 1511 update which unexpectedly
# implemented support for ANSI escape sequences.[13] The change was designed to
# complement the Windows Subsystem for Linux, adding to the Windows Console Host
# used by Command Prompt support for character escape codes used by terminal-based
# software for Unix-like systems.
# This is not the default behavior and must be enabled programmatically with the
#  Win32 API via SetConsoleMode(handle, ENABLE_VIRTUAL_TERMINAL_PROCESSING).[14]
# This was enabled by CMD.EXE but not initially by PowerShell;[15] however,
# Windows PowerShell 5.1 now enables this by default. The ability to make a
# string constant containing ESC was added in PowerShell 6 with (for example)
# "`e[32m";[16] for PowerShell 5 you had to use [char]0x1B+"[32m".


class Stylish:
    """
    This is basically a namespace, since the core functionality is implemented
    as classmethods.

    However an instance is required to use a context manager.
    Examples:

        with Stylish("yellow", bg="blue"):
            print("hey")

    """

    #: (bool)
    _enabled = False
    _initialized = False

    def __init__(self, fg, bg=None, bold=False, underline=False, italic=False):
        self.format = (fg, bg, bold, underline, italic)

    def __enter__(self):
        print(self.ansi(*self.format), end="")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(self.reset(*self.format), end="")

    @classmethod
    def _initialize(cls):
        """"""
        if cls._initialized:
            return
        cls._initialized = True
        # Shim to make colors work on Windows 10
        # See https://github.com/feluxe/sty/issues/2
        if sys.platform == "win32":
            os.system("color")

    # TODO:
    # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences

    @classmethod
    def enable(cls, flag, force=False):
        if flag and not force and not sys.stdout.isatty():
            print("SSS", sys.stdout.isatty())
            flag = False

        if flag:
            cls._initialize()
        cls._enabled = flag

    @classmethod
    def is_enabled(cls):
        return cls._enabled

    @classmethod
    def reset_all(cls):
        return EFFECT_MAP.get("reset_all")

    @classmethod
    def reset(cls, fg=True, bg=True, bold=True, underline=True, italic=True):
        if not cls._enabled:
            return ""
        if fg and bg and bold and underline and italic:
            return cls.reset_all()

        sl = []
        if fg:
            sl.append(EFFECT_MAP["reset_fg"])
        if bg:
            sl.append(EFFECT_MAP["reset_bg"])
        if bold:
            sl.append(EFFECT_MAP["reset_bold_dim"])
        if underline:
            sl.append(EFFECT_MAP["reset_underline"])
        if italic:
            sl.append(EFFECT_MAP["reset_italic"])
        res = "".join(sl)
        return res

    @classmethod
    def ansi(cls, fg, bg=None, bold=False, underline=False, italic=False):
        if not cls._enabled:
            return ""
        sl = []

        if fg is not None:
            # TODO: in simple cases, fg and bg can be combined into a single sequence
            if isinstance(fg, (list, tuple)):
                sl.append(rgb_fg(*fg))
            else:
                sl.append(FG_MAP[fg])

        if bg is not None:
            if isinstance(bg, (list, tuple)):
                sl.append(rgb_bg(*bg))
            else:
                sl.append(BG_MAP[bg])
        # Effects
        if bold:
            sl.append(EFFECT_MAP["bold"])
        if underline:
            sl.append(EFFECT_MAP["underline"])
        if italic:
            sl.append(EFFECT_MAP["italic"])
        return "".join(sl)

    @classmethod
    def wrap(cls, text, fg, bg=None, bold=False, underline=False, italic=False):
        """Return a colorized text using ANSI escape codes.

        See also: https://en.wikipedia.org/wiki/ANSI_escape_code

        When
        Examples:
            print("Hello " + color("beautiful", "green") + " world.")
        """
        if not cls._enabled:
            return text
        sl = []
        sl.append(cls.ansi(fg=fg, bg=bg, bold=bold, underline=underline, italic=italic))
        if text is not None:
            sl.append(text)
            # Only reset what we have set before
            sl.append(
                cls.reset(fg=fg, bg=bg, bold=bold, underline=underline, italic=italic)
            )

        text = "".join(str(s) for s in sl)
        return text

    @classmethod
    def set_cursor(cls, x, y, apply=True):
        # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
        if not cls._enabled:
            return ""
        ansi = ""
        if apply:
            print(ansi, end="")
        return ansi


def enable_colors(flag=True, force=False):
    return Stylish.enable(flag, force)


def colors_enabled():
    return Stylish.is_enabled()


def ansi_reset(fg=True, bg=True, bold=True, underline=True, italic=True):
    """Reset color attributes to console default."""
    return Stylish.reset(fg, bg, bold, underline, italic)


def ansi(fg, bg=None, bold=False, underline=False, italic=False):
    """Return ANSI control string that enables the requested console formatting."""
    return Stylish.ansi(fg, bg, bold, underline, italic)


def wrap(text, fg, bg=None, bold=False, underline=False, italic=False):
    """Wrap text in ANSI sequences that enable and disable console formatting."""
    return Stylish.wrap(text, fg, bg, bold, underline, italic)


def set_cursor(x, y):
    return Stylish.set_cursor(x, y)


def red(text):
    return wrap(text, "li_red")


def yellow(text):
    return wrap(text, "li_yellow")


def green(text):
    return wrap(text, "green")


def gray(text):
    return wrap(text, "li_black")


if __name__ == "__main__":
    enable_colors(True)

    with Stylish("li_yellow", bg="blue"):
        print("yellow on blue")

    with Stylish((255, 255, 0), bg=(0, 0, 255)):
        print("yellow on blue (rgb)")

    with Stylish("li_white", bg="black"):
        print("white on black")

    with Stylish((255, 255, 255), bg="black"):
        print("white on black (rgb)")

    print("before " + red("reddish") + " after")
    print("before " + yellow("yellow") + " after")
    print("before " + wrap("yellow on blue", "yellow", bg="blue") + " after")
    print("before " + wrap("green underlined", "green", underline=True) + " after")
    print("before " + wrap("blue bold", "blue", bold=True) + " after")
    print("before " + wrap("red italic", "red", italic=True) + " after")

    for color in FG_MAP.keys():
        print(wrap(color, color), end=", ")
    print(".")

    for color in BG_MAP.keys():
        print(wrap(color, None, bg=color), end=", ")
    print(".")
