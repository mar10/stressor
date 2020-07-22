# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import logging
import os
import platform
import random
import re
import sys
import types
import warnings
from datetime import datetime
from urllib.parse import urljoin, urlparse

from dateutil.parser import isoparse

from stressor import __version__

logger = logging.getLogger("stressor")

# Use logger.important("message even in -q mode")
LOGLEVEL_IMPORTANT = logging.WARNING + 1
logging.addLevelName(LOGLEVEL_IMPORTANT, "NOTE")


def log_important(self, message, *args, **kws):
    if self.isEnabledFor(LOGLEVEL_IMPORTANT):
        # Yes, logger takes its '*args' as 'args'.
        self._log(LOGLEVEL_IMPORTANT, message, args, **kws)


logging.Logger.important = log_important


#: Check if a a string may be used as YAML dictionary key without using quotes.
#: NOTE: YAML evaluates `0_` as "0" and `0_1_` as "1", so we don't accept leading numbers
RE_YAML_KEYWORD = re.compile(r"^[a-zA-Z_]+\w*$")

PYTHON_VERSION = "{}.{}.{}".format(
    sys.version_info[0], sys.version_info[1], sys.version_info[2]
)
version_info = "stressor/{} Python/{}({} bit) {}".format(
    __version__,
    PYTHON_VERSION,
    "64" if sys.maxsize > 2 ** 32 else "32",
    platform.platform(),
)


class StressorError(RuntimeError):
    """Base class for all exception that we deliberatly throw."""


class NO_DEFAULT:
    """Used as default parameter to distinguish from `None`."""


# class Singleton(type):
#     """
#     See also https://stackoverflow.com/a/6798042/19166

#     Example::

#         class Logger(metaclass=Singleton):
#             pass

#     """

#     _instances = {}

#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]


class _VOID_SEGMENT:
    """Used internally."""


class PathStack:
    """
    Examples::

        path = PathStack()
        with path.enter("level_1"):
            print("Current location: {}".format(path))
    """

    def __init__(self, root_name=None, delimiter="/"):
        self.stack = []
        self.delimiter = delimiter
        if root_name:
            self.push(root_name)

    def __str__(self):
        return self.get_path()
        # stack = (str(s) for s in self.stack if s is not _VOID_SEGMENT)
        # return self.delimiter + self.delimiter.join(stack)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pop()

    def enter(self, name, ignore=False):
        if ignore:
            self.push(_VOID_SEGMENT)
        else:
            self.push(name)
        return self

    def level(self):
        return len(self.stack)

    def push(self, name):
        self.stack.append(name)

    def pop(self):
        return self.stack.pop()

    def get_path(self, skip_segs=0, last_seg=None):
        stack = [str(s) for s in self.stack if s is not _VOID_SEGMENT]
        if skip_segs > 0:
            stack = stack[skip_segs:]
        if last_seg is not None:
            stack = stack[:-1]
            stack.append(last_seg)
        return self.delimiter + self.delimiter.join(stack)


def timetag(seconds=True, ms=False):
    """Return a time stamp string that can be used as (part of a) filename (also sorts well)."""
    now = datetime.now()
    if ms or seconds:
        s = now.strftime("%Y%m%d_%H%M%S")
        if ms:
            s = "{}_{}".format(s, now.microsecond)
    else:
        s = now.strftime("%Y%m%d_%H%M")
    return s


def init_logging(verbose=3, path=None):
    """CLI calls this."""
    if verbose < 1:
        level = logging.CRITICAL
    elif verbose < 2:
        level = logging.ERROR
    elif verbose < 3:
        level = logging.WARNING
    elif verbose < 4:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        # format="%(asctime)s.%(msecs)03d <%(thread)d> %(levelname)-7s %(message)s",
        format="%(asctime)-8s.%(msecs)-3d <%(thread)05d> %(levelname)-7s %(message)s",
        # format="%(asctime)s.%(msecs)03d <%(process)d.%(thread)d> %(levelname)-8s %(message)s",
        # fmt='%(asctime)s.%(msecs)03d',datefmt='%Y-%m-%d,%H:%M:%S')
        # format="%(asctime)s.%(msecs)d <%(process)d.%(thread)d> %(message)s",
        datefmt="%H:%M:%S",
    )

    if path:
        if os.path.isdir(path):
            fname = "stressor_{}.log".format(timetag())
            path = os.path.join(path, fname)
        logger.info("Writing log to '{}'".format(path))
        if os.path.isfile(path):
            logger.warning("Removing log file '{}'".format(path))
            os.remove(path)
        hdlr = logging.FileHandler(path)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)-3d - %(levelname)s: %(message)s", "%H:%M:%S"
        )
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        # logger.setLevel(logging.DEBUG)
        logger.info("Start log ({})".format(datetime.now()))
        logger.info(version_info)
        logger.info("Running {}".format(" ".join(sys.argv)))

        # redirect `logger` to our special log file as well:
        logger.addHandler(hdlr)

    # Silence requests `InsecureRequestWarning` messages
    if verbose < 3:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    else:
        warnings.filterwarnings("once", message="Unverified HTTPS request")

    return logger


def set_console_ctrl_handler(
    ctrl_handler, do_ctrl_c=True, do_ctrl_break=False, do_ctrl_close=False
):
    """

    The do_ctrl_* functions could simply be sys.exit(1), which will ensure that
    atexit handlers get called.
    See https://bugs.python.org/issue35935

    Raises:
        ctypes.WinError
    Returns:
        False if not on Windows or could not register the handler.
    """
    if os.name != "nt":
        return False

    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        logger.info("Loaded kernel32 DLL on Windows.")
    except Exception as e:
        logger.warning("Could not load kernel32 DLL on Windows: {}".format(e))
        return False

    CTRL_C_EVENT = 0
    CTRL_BREAK_EVENT = 1
    CTRL_CLOSE_EVENT = 2

    HANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    kernel32.SetConsoleCtrlHandler.argtypes = (HANDLER_ROUTINE, wintypes.BOOL)

    @HANDLER_ROUTINE
    def handler(ctrl):
        if ctrl == CTRL_C_EVENT and do_ctrl_c:
            handled = ctrl_handler(ctrl)
        elif ctrl == CTRL_BREAK_EVENT and do_ctrl_break:
            handled = ctrl_handler(ctrl)
        elif ctrl == CTRL_CLOSE_EVENT and do_ctrl_close:
            handled = ctrl_handler(ctrl)
        else:
            handled = False
        # If not handled, call the next handler.
        return handled

    if not kernel32.SetConsoleCtrlHandler(handler, True):
        raise ctypes.WinError(ctypes.get_last_error())
    return True


def assert_always(condition, msg=None):
    """`assert` even in production code."""
    try:
        if not condition:
            raise AssertionError(msg) if msg is not None else AssertionError
    except AssertionError as e:
        if sys.version_info < (3, 7):
            raise
        # Strip last frames, so the exception's stacktrace points to the call
        # Credits: https://stackoverflow.com/a/58821552/19166
        _exc_type, _exc_value, traceback = sys.exc_info()
        back_frame = traceback.tb_frame.f_back

        back_tb = types.TracebackType(
            tb_next=None,
            tb_frame=back_frame,
            tb_lasti=back_frame.f_lasti,
            tb_lineno=back_frame.f_lineno,
        )
        raise e.with_traceback(back_tb)


def _check_arg(argument, types, condition, accept_none):
    if __debug__:
        err_msg = "`allowed_types` must be a type or class (or a tuple thereof): got instance of {}"
        if isinstance(types, tuple):
            for t in types:
                assert isinstance(t, type), err_msg.format(type(t))
        else:
            assert isinstance(types, type), err_msg.format(type(types))

    if accept_none:
        if argument is None:
            return
        extra_msg = "`None` or "
    else:
        extra_msg = ""

    if not isinstance(argument, types):
        raise TypeError(
            "Expected {}{}, but got {}".format(extra_msg, types, type(argument))
        )
    if condition is not NO_DEFAULT and not bool(condition):
        raise ValueError(
            "Invalid argument value: {} {}".format(type(argument), argument)
        )


def check_arg(argument, allowed_types, condition=NO_DEFAULT, or_none=False):
    """Check if `argument` has the expected type and value.

    **Note:** the exception's traceback is manipulated, so that the back frame
    points to the ``check_arg()`` line, instead of the actual ``raise``.

    Args:
        argument (any): value of the argument to check
        allowed_types (type or tuple of types)
        condition (bool, optional): additional condition that must be true
        or_none (bool, optional): defaults to false
    Returns:
        None
    Raises:
        TypeError: if `argument` is of an unexpected type
        ValueError: if `argument` does not fulfill the optional condition
        AssertionError:
            if `check_arg` was called with a wrong syntax, i.e. `allowed_types`
            does not contain types, e.g. if `1` was passed instead of `int`.

    Examples::

        def foo(name, amount, options=None):
            check_arg(name, str)
            check_arg(amount, (int, float), amount > 0)
            check_arg(options, dict, or_none=True)
    """
    try:
        _check_arg(argument, allowed_types, condition, accept_none=or_none)
    except (TypeError, ValueError) as e:
        if sys.version_info < (3, 7):
            raise
        # Strip last frames, so the exception's stacktrace points to the call
        _exc_type, _exc_value, traceback = sys.exc_info()
        back_frame = traceback.tb_frame.f_back

        back_tb = types.TracebackType(
            tb_next=None,
            tb_frame=back_frame,
            tb_lasti=back_frame.f_lasti,
            tb_lineno=back_frame.f_lineno,
        )
        raise e.with_traceback(back_tb)


def get_dict_attr(d, key_path, default=NO_DEFAULT):
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
    if default is not NO_DEFAULT:
        try:
            return get_dict_attr(d, key_path)
        except (AttributeError, KeyError, ValueError, IndexError):
            return default

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
            # raise ValueError("Segment '{}' cannot be nested".format(seg))
            try:
                value = getattr(value, seg)
            except AttributeError:
                raise  # ValueError("Segment '{}' cannot be nested".format(seg))

    return value


def parse_args_from_str(arg_str, arg_defs):  # , context=None):
    """
    Args:
        args_str (str): argument string, optionally comma-separated
        arg_defs (tuple): list of argument definitions
        context (dict, optional):
            When passed, the arguments  are parsed for ``$(var_name)`` macros,
            to lookup values from that dict.
    Returns:
        (dict) keyword args
    Raises:
        TypeError: if `argument` is of an unexpected type
        ValueError: if `argument` does not fulfill the optional condition
        AssertionError:
            if `parse_args_from_str` was called with a wrong syntax, i.e.
            `arg_defs` is not well-formed.

    Examples::

        arg_defs = (
            ("name", str),
            ("amount", float),
            ("options", dict, {}),
        )
        def order(raw_arg_string):
            kwargs = parse_args_from_str(arg_defs)
            assert isisnstance(kwargs["name"], str)
            assert type(kwargs["amount"]) is float
            assert isisnstance(kwargs["options"], dict)
    """
    check_arg(arg_str, str)
    check_arg(arg_defs, (list, tuple))

    res = {}

    # Special case: '$name()' should not be interpreted as having one "" arg
    # if arg_defs defines a default for the first arg
    if arg_str.strip() == "" and len(arg_defs[0]) == 3:
        arg_str = str(arg_defs[0][2])

    arg_list = [a.strip() for a in arg_str.split(",")]
    optional_mode = False
    for arg_def in arg_defs:
        check_arg(arg_def, (list, tuple))
        if len(arg_def) == 2:
            arg_name, arg_type = arg_def
            arg_default = NO_DEFAULT
            if optional_mode:
                raise AssertionError(
                    "Mandatory arg definition must not follow optional args: `{}`".format(
                        arg_def
                    )
                )
        elif len(arg_def) == 3:
            arg_name, arg_type, arg_default = arg_def
            optional_mode = True
        else:
            raise AssertionError("Expected 2- or 3-tuple: {}".format(arg_def))

        if arg_type not in (float, int, str):
            raise AssertionError(
                "Unsupported argument definition type: {}".format(arg_def)
            )

        try:
            # Get next arg
            arg_val = arg_list.pop(0)
            # Allow quotes
            is_quoted = (arg_val.startswith('"') and arg_val.endswith('"')) or (
                arg_val.startswith("'") and arg_val.endswith("'")
            )
            if is_quoted:
                # Strip quotes and return as string (don't cast to other types)
                arg_val = arg_val[1:-1]
            elif "$(" in arg_val:
                # The arg seems to be a macro: don't try to cast.
                pass
            else:
                # Raises ValueError:
                arg_val = arg_type(arg_val)
        except IndexError:
            if arg_default is NO_DEFAULT:
                raise ValueError(
                    "Missing mandatory arg `{}` in '{}'.".format(arg_name, arg_str)
                )
            arg_val = arg_default

        res[arg_name] = arg_val

    if arg_list:
        raise ValueError("Extra args `{}`.".format(", ".join(arg_list)))

    return res


def is_yaml_keyword(s):
    """Return true if `s` is a JSON compatible key."""
    return bool(s and RE_YAML_KEYWORD.match(s))


# def is_abs_url(url):
#     """Return true if url is already absolute."""
#     return "://" in url or url.startswith("/")


def is_relative_url(url):
    """Return true if url is relative to the server."""
    return "://" not in url  # or url.startswith("/")


def resolve_url(root, url):
    """Convert relative URL to absolute, using `root` as default."""
    return urljoin(root, url)


def base_url(url):
    parsed_uri = urlparse(url)
    if parsed_uri.netloc:
        res = "{uri.scheme}://{uri.netloc}{uri.path}".format(uri=parsed_uri)
    else:
        res = "{uri.path}".format(uri=parsed_uri)
    return res


def shorten_string(long_string, max_chars, min_tail_chars=0, place_holder="[...]"):
    """Return string, shortened to max_chars characters.

    long_string = "This is a long string, that will be truncated."
    trunacated_string = truncate_string(long_string, max_chars=26, min_tail_chars=11, place_holder="[...]")
    print trunacated_string
    >> This is a [...] truncated.

    @param long_string: string to be truncated
    @param max_chars: max chars of returned string
    @param min_tail_chars: minimum of tailing chars
    @param place_holder: place holder for striped content
    @return: truncated string
    """

    assert max_chars > (min_tail_chars + len(place_holder))

    # Other types aren't supported.
    if not isinstance(long_string, str):
        return long_string

    # If string is shorter then max_chars, it can be returned, as is.
    elif len(long_string) <= max_chars:
        return long_string

    # Making sure we don't exceed max_chars in total.
    prefix_length = max_chars - min_tail_chars - len(place_holder)

    if min_tail_chars:
        long_string = (
            long_string[:prefix_length] + place_holder + long_string[-min_tail_chars:]
        )
    else:
        long_string = long_string[:prefix_length] + place_holder

    assert len(long_string) == max_chars

    return long_string


def get_random_number(num_or_tuple):
    check_arg(num_or_tuple, (int, float, list, tuple), or_none=True)

    if isinstance(num_or_tuple, (tuple, list)):
        v = random.uniform(*num_or_tuple)
    elif num_or_tuple:
        v = float(num_or_tuple)
    else:
        v = num_or_tuple
    return v


def datetime_to_iso(dt=None, microseconds=False):
    """Return current UTC datetime as ISO formatted string."""
    if dt is None:
        dt = datetime.now()
    if not microseconds:
        dt.replace(microsecond=0)
    return dt.isoformat(sep=" ")


def iso_to_datetime(iso):
    """Convert as ISO formatted datetime string to datetime."""
    # dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%fZ")
    dt = isoparse(iso)

    return dt


def iso_to_stamp(iso):
    """Convert as ISO formatted datetime string to datetime."""
    return iso_to_datetime(iso).timestamp()


def format_elap(seconds, count=None, unit="items", high_prec=False):
    """Return elapsed time as H:M:S.h string with reasonable precision."""
    days, seconds = divmod(seconds, 86400) if seconds else (0, 0)

    if seconds >= 3600:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if high_prec:
            res = "{:d}:{:02d}:{:04.1f} hrs".format(int(h), int(m), s)
        else:
            res = "{:d}:{:02d}:{:02d} hrs".format(int(h), int(m), int(s))
    elif seconds >= 60:
        m, s = divmod(seconds, 60)
        if high_prec:
            res = "{:d}:{:05.2f} min".format(int(m), s)
        else:
            res = "{:d}:{:02d} min".format(int(m), int(s))
    else:
        if high_prec:
            res = "{:.3f} sec".format(seconds)
        elif seconds > 5:
            res = "{:.1f} sec".format(seconds)
        else:
            res = "{:.2f} sec".format(seconds)

    if days == 1:
        res = "{} day {}".format(int(days), res)
    elif days:
        res = "{} days {}".format(int(days), res)

    if count and (seconds > 0):
        res += ", {:,.1f} {}/sec".format(float(count) / seconds, unit)
    return res


def format_rate(count, time, unit=None, high_prec=False):
    """Return count / time with reasonable precision."""
    if not time or not count:
        return "0"

    rate = float(count) / float(time)
    if rate >= 1000:
        res = "{}".format(int(round(rate)))
    elif rate >= 100:
        res = "{}".format(round(rate, 1))
    elif rate >= 10:
        res = "{}".format(round(rate, 2))
    else:
        res = "{}".format(round(rate, 3))
    return res


# def format_relative_datetime(dt, as_html=False):
#     """Format a datetime object as relative expression (i.e. '3 minutes ago')."""
#     try:
#         diff = datetime.utcnow() - dt
#         res = None
#         s = diff.seconds

#         if diff.days > 7 or diff.days < 0:
#             res = dt.strftime("%d %b %y")
#         elif diff.days == 1:
#             res = "1 day ago"
#         elif diff.days > 1:
#             res = "{} days ago".format(diff.days)
#         elif s <= 1:
#             res = "just now"
#         elif s < 60:
#             res = "{} seconds ago".format(s)
#         elif s < 120:
#             res = "1 minute ago"
#         elif s < 3600:
#             res = "{} minutes ago".format(s/60)
#         elif s < 7200:
#             res = "1 hour ago"
#         else:
#             res = "{} hours ago".format(s/3600)

#         if as_html:
#             dts = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
#             res = "<span title='{dt}'>{rel}</span>".format(rel=res, dt=dts)

#     except Exception:
#         log_exception("invalid dt: {}".format(dt))
#         res = "(invalid {})".format(dt)
#     return res


# def format_relative_stamp(stamp, as_html=False):
#     dt = stamp_to_datetime(stamp)
#     return format_relative_datetime(dt, as_html)


# def string_to_bool(arg_, default=None):
#     """Return boolean for various bool string representations.

#     Raises Error, if string is not compatible, and no default was passed.
#     """
#     if not default in (None, True, False):
#         raise TypeError("default must be None or boolean")
#     if arg_ is None:
#         if default in (True, False):
#             return default
#         else: #default == None
#             raise ValueError("Argument is %r and default %r." % (arg_, default))
#     else:
#         if arg_ in (True, False):
#             # `bool` is a subclass of `int`, so we get here for 0 and 1 as well!
#             return bool(arg_)
#         arg = arg_.lower().strip()
#         if arg in ("1", "true", "on", "yes"):
#             return True
#         elif arg in ("0", "false", "off", "no"):
#             return False
#         elif default is not None:
#             return default
#     raise ValueError("Argument string is not boolean: %r default: %r." % (arg_, default))


# def byteNumberString(number, thousandsSep=True, partition=False,
#                      base1024=True, appendBytes="iec", prec=0):
#     """Convert bytes into human-readable representation."""
#     magsuffix = ""
#     bytesuffix = ""
#     assert appendBytes in (False, True, "short", "iec")
#     if partition:
#         magnitude = 0
#         if base1024:
#             while number >= 1024:
#                 magnitude += 1
# #                 number = number >> 10
#                 number /= 1024.0
#         else:
#             while number >= 1000:
#                 magnitude += 1
#                 number /= 1000.0
#         # TODO:
#         # Windows 7 Explorer teilt durch 1024, und verwendet trotzdem KB statt KiB.
#         # Außerdem wird aufgerundet: --> 123 -> "1 KB"
#         # http://en.wikipedia.org/wiki/Kibi-#IEC_standard_prefixes
#         magsuffix = ["", "K", "M", "G", "T", "P"][magnitude]
#         if magsuffix:
#             magsuffix = " " + magsuffix

#     if appendBytes:
#         if appendBytes == "iec" and magsuffix:
#             bytesuffix = "iB" if base1024 else "B"
#         elif appendBytes == "short" and magsuffix:
#             bytesuffix = "B"
#         elif number == 1:
#             bytesuffix = " Byte"
#         else:
#             bytesuffix = " Bytes"

#     if thousandsSep and (number >= 1000 or magsuffix):
#         locale.setlocale(locale.LC_ALL, "")
#         # TODO: make precision configurable
#         if prec > 0:
#             fs = "%.{}f".format(prec)
#             snum = locale.format_string(fs, number, thousandsSep)
#         else:
#             snum = locale.format("%d", number, thousandsSep)
#         # Some countries like france use non-breaking-space (hex=a0) as group-
#         # seperator, that's not plain-ascii, so we have to replace the hex-byte
#         # "a0" with hex-byte "20" (space)
#         snum = hexlify(snum).replace("a0", "20").decode("hex")
#     else:
#         snum = str(number)

#     return "%s%s%s" % (snum, magsuffix, bytesuffix)


def lstrip_string(s, prefix, ignore_case=False):
    """Remove leading string from s.

    Note: This is different than `s.lstrip('bar')` which would remove
    all leading 'a', 'b', and 'r' chars.
    """
    if ignore_case:
        if s.lower().startswith(prefix.lower()):
            return s[len(prefix) :]
    else:
        if s.startswith(prefix):
            return s[len(prefix) :]
    return s


# def rstrip_string(s, suffix, ignore_case=False):
#     """Remove trailing string from s.

#     Note: This is different than `s.rstrip('bar')` which would remove
#     all trailing 'a', 'b', and 'r' chars.
#     """
#     if ignore_case:
#         if s.lower().endswith(suffix.lower()):
#             return s[:-len(suffix)]
#     else:
#         if s.endswith(suffix):
#             return s[:-len(suffix)]
#     return s
