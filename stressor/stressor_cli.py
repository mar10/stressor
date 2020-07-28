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
import os
import sys

import yaml

from snazzy import enable_colors
from stressor import __version__
from stressor.cli_common import common_parser, verbose_parser
from stressor.convert.har_converter import HarConverter
from stressor.run_manager import RunManager
from stressor.util import init_logging, logger, version_info


def handle_run_command(parser, args):
    options = {
        "monitor": args.monitor,
        "log_summary": True,
        "dry_run": args.dry_run,
    }
    extra_context = {
        "dry_run": args.dry_run,
    }

    scenario_fspec = args.scenario
    if os.path.isdir(scenario_fspec):
        scenario_fspec = os.path.join(scenario_fspec, "scenario.yaml")
        logger.info("Looking for {}".format(scenario_fspec))

    rm = RunManager()
    rm.load_config(scenario_fspec)
    if args.single:
        rm.config_manager.config["force_single"] = True
    if args.max_time:
        rm.config_manager.config["max_time"] = float(args.max_time)
    if args.max_errors:
        rm.config_manager.config["max_errors"] = int(args.max_errors)

    res = rm.run(options, extra_context)

    if not res:
        logger.error("Finished with errors.")
        return 1
    logger.info("Stressor run succesfully completed.")
    return 0


def handle_init_command(parser, args):
    opts = {}
    if args.opts:
        if not os.path.isfile(args.opts):
            parser.error("File not found: {}".format(args.opts))
        with open(args.opts, "rt") as f:
            opts = yaml.safe_load(f)

    opts.update(
        {
            "fspec": args.har_file,
            "target_folder": args.target,
            "force": args.force,
            "dry_run": args.dry_run,
        }
    )
    conv = HarConverter(opts)
    res = conv.run()
    return res


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
        parents=[verbose_parser, common_parser],
        # allow_abbrev=False,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="display version info and exit (combine with -v for more information)",
    )
    subparsers = parser.add_subparsers(help="sub-command help")

    # --- Create the parser for the "run" command ------------------------------

    sp = subparsers.add_parser(
        "run",
        parents=[verbose_parser, common_parser],
        help="run a test suite scenario",
    )

    sp.add_argument(
        "scenario",
        metavar="SCENARIO",
        default="./scenario.yaml",
        help="path to configuration file or folder (default: %(default)s)",
    )
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
    sp.add_argument(
        "--max-errors",
        type=int,
        default=0,
        help="Stop after N errors (overrides `config.max_errors`)",
    )
    sp.add_argument(
        "--max-time",
        type=float,
        default=0.0,
        help="Stop after N seconds (overrides `config.max_time`)",
    )

    sp.set_defaults(command=handle_run_command)

    # --- Create the parser for the "init" command ---------------------------

    sp = subparsers.add_parser(
        "init",
        parents=[verbose_parser, common_parser],
        help="create new scenario folder and optinally convert HAR files",
    )
    sp.add_argument(
        "target",
        metavar="TARGET",
        # default="./scenario.yaml",
        help="target folder (created if not existing)",
    )
    sp.add_argument(
        "--import",
        dest="har_file",
        # required=True,
        help="optional HAR file that is converted",
    )
    sp.add_argument(
        "--force", action="store_true", help="override existing files",
    )
    sp.add_argument(
        "--opts", help="YAML file with conversion options",
    )
    sp.set_defaults(command=handle_init_command)

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
    init_logging(args.verbose, args.log_file)

    if not args.no_color:
        # Enable snazzy colors and emojis if terminal supports them
        enable_colors(True, force=False)

    if getattr(args, "version", None):
        if args.verbose >= 4:
            info = version_info
            info += "\nPython from: {}".format(sys.executable)
        else:
            info = __version__
        print(info)
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
