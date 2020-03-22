# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""

import argparse

# --- verbose_parser ----------------------------------------------------------

verbose_parser = argparse.ArgumentParser(
    add_help=False,
    # allow_abbrev=False,
)

qv_group = verbose_parser.add_mutually_exclusive_group()
qv_group.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=3,
    help="increment verbosity by one (default: %(default)s, range: 0..5)",
)
qv_group.add_argument(
    "-q", "--quiet", default=0, action="count", help="decrement verbosity by one"
)


# --- common_parser ----------------------------------------------------------


common_parser = argparse.ArgumentParser(
    add_help=False,
    # allow_abbrev=False,
)
common_parser.add_argument(
    "-n",
    "--dry-run",
    action="store_true",
    help="just simulate and log results, but don't change anything",
)
common_parser.add_argument(
    "--no-color", action="store_true", help="prevent use of ansi terminal color codes"
)
common_parser.add_argument(
    "--log",
    dest="log_file",
    help="Path to log file or folder (generate unique file name in the latter case)",
)
