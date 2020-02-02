# -*- coding: utf-8 -*-
"""
Stress-test your web app.

(c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php

Usage examples:
  $ stressor --help
  $ stressor run .
"""
import argparse
import platform
import sys

from stressor import __version__
from stressor.cli_common import common_parser, verbose_parser
from stressor.run_manager import RunManager
from stressor.util import init_logging, logger


def handle_run_command(parser, args):
    # try:
    #     config = read_config(args.project, verbose=args.verbose)
    # except ConfigurationError as e:
    #     parser.error("{}".format(e))

    options = {
        "monitor": args.monitor,
        "dry_run": args.dry_run,
    }
    extra_context = {
        "dry_run": args.dry_run,
    }

    rm = RunManager()
    rm.load_config(args.project)
    if args.single:
        # if rm.sessions["count"] > 1:
        #     logger.info("Forcing run_config.sessions.count to 1.")
        rm.run_config["force_single"] = True

    res = rm.run(options, extra_context)

    if not res:
        logger.error("Finished with errors.")
        return 1
    logger.info("Stressor run succesfully completed.")
    return 0


def handle_listen_command(parser, args):
    raise NotImplementedError


# ===============================================================================
# run
# ===============================================================================
def run():
    """CLI main entry point."""

    parser = argparse.ArgumentParser(
        description="Stress-test your web app.",
        epilog="See also https://github.com/mar10/stressor",
        parents=[verbose_parser],
        # allow_abbrev=False,
    )

    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="display versin info and exit (combine with -v for more information)",
    )

    subparsers = parser.add_subparsers(help="sub-command help")

    # --- Create the parser for the "run" command ------------------------------

    sp = subparsers.add_parser(
        "run",
        parents=[verbose_parser, common_parser],
        help="run a test suite scenario",
    )

    sp.add_argument(
        "project",
        metavar="PROJECT",
        default="./project.yaml",
        help="path to configuration file (default: %(default)s)",
    )
    # sp.add_argument(
    #     "suite",
    #     metavar="SUITE",
    #     nargs="*",
    #     help="name of a suite definition in the project (multiple values allowed, default: all)",
    # )
    sp.add_argument(
        "-o",
        "--option",
        nargs="*",
        help="override configuration, syntax `OPTION:VALUE` (multiple values allowed)",
    )
    sp.add_argument(
        "--single",
        action="store_true",
        help="Force `run_config.sessions.count: 1`, so only one thread is run",
    )
    sp.add_argument(
        "--monitor",
        action="store_true",
        help="Open a web server and browser application to display real-time progress",
    )

    sp.set_defaults(command=handle_run_command)

    # --- Create the parser for the "listen" command ---------------------------

    # sp = subparsers.add_parser(
    #     "listen",
    #     parents=[verbose_parser, common_parser],
    #     help="run in 'drone' mode, listening for commands from master",
    # )

    # sp.add_argument(
    #     "--host",
    #     default="0.0.0.0",
    #     help="local ip address or hostname to bind to (default: %(default)s)",
    # )
    # sp.add_argument(
    #     "--port",
    #     type=int,
    #     default=8082,
    #     help="local port number to bind to (default: %(default)s)",
    # )
    # sp.add_argument(
    #     "--secret",
    #     default=None,
    #     help="password that master must use (default: random)",
    # )
    # sp.add_argument(
    #     "--collect",
    #     metavar="SECS",
    #     type=int,
    #     default=0,
    #     help="report ram, cpu load, and other system metrics every SECS seconds (default: off)",
    # )

    # sp.set_defaults(command=handle_listen_command)

    # --- Parse command line ---------------------------------------------------

    args = parser.parse_args()

    args.verbose -= args.quiet
    del args.quiet

    # print("verbose", args.verbose)
    init_logging(args.verbose)

    if getattr(args, "version", None):
        if args.verbose >= 4:
            PYTHON_VERSION = "{}.{}.{}".format(
                sys.version_info[0], sys.version_info[1], sys.version_info[2]
            )
            version_info = "stressor/{} Python/{} {}".format(
                __version__, PYTHON_VERSION, platform.platform()
            )
        else:
            version_info = __version__
        print(version_info)
        sys.exit(0)

    if not callable(getattr(args, "command", None)):
        parser.error("missing command")

    try:
        return args.command(parser, args)
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(3)
    # Unreachable...
    return


# Script entry point
if __name__ == "__main__":
    # Just in case...
    from multiprocessing import freeze_support

    freeze_support()

    run()
