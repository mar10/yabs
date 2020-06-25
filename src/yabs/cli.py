# -*- coding: utf-8 -*-
"""
A collection of tools for tox release workflows.

(c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php

Usage examples:
    $ yabs --help
    $ yabs check --clean --branch master
"""
import argparse
import platform
import sys

from yabs import __version__

from .cmd_common import register_cli_commands
from .log import log
from .task_runner import handle_run_command
from .util import init_logging

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
        "run", parents=parents, help="run a workflow definition",
    )
    sp.add_argument(
        "workflow", nargs="?", default="./yabs.yaml", help="run a workflow definition",
    )
    sp.add_argument(
        "--inc",
        choices=["major", "minor", "patch", "postrelease"],
        default=None,
        help="bump semantic version (used as default for `bump` tasks)",
    )
    sp.add_argument(
        "--no-bump", action="store_true", help="skip all 'bump' tasks",
    )
    sp.add_argument(
        "--no-check",
        action="store_true",
        help="don't let the 'check' task stop the workflow (log warnings instead)",
    )
    sp.add_argument(
        "--no-release",
        action="store_true",
        help="skip all 'gh-release' and 'pypi-release' tasks",
    )
    sp.set_defaults(command=handle_run_command)

    # --- Let all sublasses of `WorkflowTask` add their arguments --------------

    register_cli_commands(subparsers, parents)

    # --- Parse command line ---------------------------------------------------

    args = parser.parse_args()

    args.verbose -= args.quiet
    del args.quiet

    # print("verbose", args.verbose)
    init_logging(args.verbose)  # , args.log_file)

    if not args.no_color and sys.stdout.isatty():
        log.enable_color(True)

    if getattr(args, "version", None):
        if args.verbose >= 4:
            PYTHON_VERSION = "{}.{}.{}".format(
                sys.version_info[0], sys.version_info[1], sys.version_info[2]
            )
            version_info = "yabs/{} Python/{} {}".format(
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
