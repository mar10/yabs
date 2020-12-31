# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

from git import Repo

from .cmd_common import WorkflowTask
from .util import ConfigError, check_arg, log_error, log_warning
from .version_manager import INCREMENTS, ORDERED_INCREMENTS


class BumpTask(WorkflowTask):
    DEFAULT_OPTS = {
        "inc": None,
        "check": True,
        "prerelease_prefix": "a",
        "prerelease_start_idx": 1,
    }

    def __init__(self, opts):
        super().__init__(opts)
        opts = self.opts
        check_arg(
            opts["inc"], str, or_none=True, condition=opts.get("inc") in INCREMENTS
        )
        check_arg(opts["check"], bool)
        check_arg(opts["prerelease_prefix"], str)

    def to_str(self, context):
        if context:
            inc = self.opts["inc"] or context.inc
            version = context.version_manager.master_version
            return "{}({!r}) => v{}".format(self.__class__.__name__, inc, version)
        return "{}({!r})".format(self.__class__.__name__, self.opts["inc"])

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""
        # Additional arguments for the 'run' command
        run_parser.add_argument(
            "--inc",
            choices=["major", "minor", "patch", "postrelease"],
            default=None,
            help="bump semantic version (used as default for `bump` task's `inc` option)",
        )
        run_parser.add_argument(
            "--no-bump",
            action="store_true",
            help="run all 'bump' tasks in dry-run mode",
        )

    @classmethod
    def check_task_def(cls, task_def, parser, args, yaml):
        # We cannot check if we don't have CLI args (like in test fixtures)
        if not args:
            return True
        if args.no_bump:
            return True
        inc = task_def.get("inc") or args.inc
        if not inc:
            return "'bump' tasks require `--inc` argument or `inc` option"
        config = yaml["config"]
        max_increment = config.get("max_increment", "minor")
        max_idx = ORDERED_INCREMENTS.index(max_increment)
        inc_idx = ORDERED_INCREMENTS.index(inc)
        if inc_idx > max_idx:
            if args.force:
                log_warning(
                    "Enforcing `--inc {}` although `max_increment` option is set to '{}'".format(
                        args.inc, max_increment
                    )
                )
            else:
                return (
                    "`--inc {}` was passed, but the `max_increment` option is set to '{}'"
                    " (pass `--force` to ignore).".format(args.inc, max_increment)
                )
        return True

    def run(self, context):
        opts = self.opts
        dry_run = context.dry_run
        if context.args.no_bump:
            log_warning("`--no-bump` was passed: forcing dry-run mode for 'bump' task.")
            dry_run = True

        inc = opts.get("inc")
        if not inc:
            if context.inc:
                inc = context.inc
            else:
                raise ConfigError(
                    "Missing bump increment: either define `inc` option or pass `--inc` argument."
                )

        if inc not in INCREMENTS:
            raise ConfigError(
                "Invalid `inc` option '{}' (expected {}).".format(
                    inc, ", ".join(INCREMENTS)
                )
            )

        org_version = context.org_version
        is_prerelease = org_version.prerelease if org_version else False
        if context.args.inc == "postrelease" and not opts.get("inc") and is_prerelease:
            # If `--inc postrelease` was passed and the bump-task does not
            # explicitly define `inc: postrelease`, untagged post-releases are
            # not bumped again.
            repo_path = os.path.abspath(".")
            repo = Repo(repo_path)
            try:
                repo.tag(str(org_version))
            except ValueError:
                log_warning(
                    "Bump '--inc postrelease' is ignored, because current version {} "
                    "is already a prerelease and not yet tagged.".format(org_version)
                )
                log_warning(
                    "Following task will tag and release {}.".format(org_version)
                )
                return True

        vm = context.version_manager
        vm.bump(inc, prerelease_prefix=opts["prerelease_prefix"], write=not dry_run)
        context.version = vm.master_version

        if opts["check"] and not dry_run:
            _ret_code, real_version = self._exec(["python", "setup.py", "--version"])
            if real_version != str(vm.master_version):
                log_error(
                    "`setup.py --version` returned {} (expected {}).".format(
                        real_version, vm.master_version
                    )
                )
                return False

        return True
