# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import logging
import sys
import types
import warnings

logger = logging.getLogger("stressor")


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
        self.stack = []  # parent.stack if parent else []
        self.delimiter = delimiter
        if root_name:
            self.push(root_name)

    def __str__(self):
        stack = (str(s) for s in self.stack if s is not _VOID_SEGMENT)
        return self.delimiter + self.delimiter.join(stack)

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


def init_logging(verbose=3):
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

    # Silence requests `InsecureRequestWarning` messages
    if verbose < 3:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    else:
        warnings.filterwarnings("once", message="Unverified HTTPS request")

    return logger


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
        ValueError: if `argument` does not fulfil the optional condition
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
        else:
            res = "{:.1f} sec".format(seconds)

    if days == 1:
        res = "{} day {}".format(int(days), res)
    elif days:
        res = "{} days {}".format(int(days), res)

    if count and (seconds > 0):
        res += ", {:,.1f} {}/sec".format(float(count) / seconds, unit)
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


# def lstrip_string(s, prefix, ignore_case=False):
#     """Remove leading string from s.

#     Note: This is different than `s.lstrip('bar')` which would remove
#     leading 'b', 'a', and 'r' chars.
#     """
#     if ignore_case:
#         if s.lower().startswith(prefix.lower()):
#             return s[len(prefix):]
#     else:
#         if s.startswith(prefix):
#             return s[len(prefix):]
#     return s


# def rstrip_string(s, suffix, ignore_case=False):
#     """Remove trailing string from s.

#     Note: This is different than `s.rstrip('bar')` which would remove
#     trailing 'b', 'a', and 'r' chars.
#     """
#     if ignore_case:
#         if s.lower().endswith(suffix.lower()):
#             return s[:-len(suffix)]
#     else:
#         if s.endswith(suffix):
#             return s[:-len(suffix)]
#     return s
