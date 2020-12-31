# -*- coding: utf-8 -*-
"""
A collection of tools for tox release workflows.

(c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php

Usage examples:
    $ yabs --help
    $ yabs check --clean --branch master
"""
import argparse
import logging
import platform
import sys

from snazzy import enable_colors

from yabs import __version__

from .plugin_manager import PluginManager
from .task_runner import handle_run_command
from .util import check_cli_verbose, init_logging

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


# ===============================================================================
# run
# ===============================================================================
def run():
    """CLI main entry point."""

    parents = [verbose_parser, common_parser]

    parser = argparse.ArgumentParser(
        description="Release workflow automation tools.",
        epilog="See also https://github.com/mar10/yabs",
        parents=parents,
        # allow_abbrev=False,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="display version info and exit (combine with -v for more information)",
    )
    subparsers = parser.add_subparsers(help="sub-command help")

    # --- Create the parser for the "run" command -----------------------------

    sp = subparsers.add_parser(
        "run",
        parents=parents,
        help="run a workflow definition",
    )
    sp.add_argument(
        "workflow",
        nargs="?",
        default="./yabs.yaml",
        help="run a workflow definition",
    )
    sp.add_argument(
        "--force",
        action="store_true",
        help="allow to ignore some errors (like bumping above `max_increment`)",
    )
    sp.add_argument(
        "--no-release",
        action="store_true",
        help="don't upload tags and assets to GitHub or PyPI (but still build assets)",
    )
    sp.set_defaults(command=handle_run_command)
    run_parser = sp

    # --- Let all sublasses of `WorkflowTask` add their arguments --------------
    # We want to see some logging, even if init_logging() wasn't called yet:
    level = logging.DEBUG if check_cli_verbose() >= 4 else logging.INFO
    logging.basicConfig(level=level, format="%(message)s", datefmt="%H:%M:%S")
    PluginManager.register_cli_commands(subparsers, parents, run_parser)

    # --- Parse command line ---------------------------------------------------

    args = parser.parse_args()

    args.verbose -= args.quiet
    del args.quiet

    # print("verbose", args.verbose)
    init_logging(args.verbose)  # , args.log_file)

    if not args.no_color:
        # Enable terminal colors (if sys.stdout.isatty())
        enable_colors(True, force=False)

    if getattr(args, "version", None):
        if args.verbose >= 4:
            PYTHON_VERSION = "{}.{}.{}".format(
                sys.version_info[0], sys.version_info[1], sys.version_info[2]
            )
            version_info = "yabs/{} Python/{}({} bit) {}".format(
                __version__,
                PYTHON_VERSION,
                "64" if sys.maxsize > 2 ** 32 else "32",
                platform.platform(),
            )
            version_info += "\nPython from: {}".format(sys.executable)
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
