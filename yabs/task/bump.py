# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from typing import TYPE_CHECKING

from ..util import ConfigError, check_arg, log_error, log_info, log_warning
from ..version_manager import INCREMENTS, ORDERED_INCREMENTS
from .common import SkipTaskResult, TaskContext, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class BumpTask(WorkflowTask):
    DEFAULT_OPTS = {
        "inc": None,
        "check": True,
        "prerelease_prefix": "a",
        "prerelease_start_idx": 1,
    }
    MANDATORY_OPTS = None

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(
            opts["inc"], str, or_none=True, condition=opts.get("inc") in INCREMENTS
        )
        check_arg(opts["check"], bool)
        check_arg(opts["prerelease_prefix"], str)
        check_arg(opts["prerelease_start_idx"], int)
        self.version_before_bump = None

    def to_str(self, context: TaskContext):
        name = self.__class__.__name__
        if context:
            inc = self.opts["inc"] or context.inc
            version = context.version_manager.master_version
            if self.version_before_bump:
                return f"{name}({inc!r}) v{self.version_before_bump} => v{version}"
            return f"{name}({inc!r}) => v{version}"
        return "{}({!r})".format(name, self.opts["inc"])

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
        run_parser.add_argument(
            "--force-pre-bump",
            action="store_true",
            help="bump `--inc postrelease` even if the current version is untagged",
        )

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        # We cannot check if we don't have CLI args (like in test fixtures)
        # args = task_inst.task_runner.args
        task_runner = task_inst.task_runner
        cli_arg = task_runner.cli_arg
        config = task_runner.config
        task_def = task_inst.task_def

        if task_runner.command != "run":
            return True  # 'info' or not CLI
        if cli_arg("no_bump"):
            return True
        inc = task_def.get("inc") or cli_arg("inc")
        if not inc:
            return "'bump' tasks require `--inc` argument or `inc` option"
        max_increment = config.get("max_increment", "minor")
        max_idx = ORDERED_INCREMENTS.index(max_increment)
        inc_idx = ORDERED_INCREMENTS.index(inc)
        if inc_idx > max_idx:
            if cli_arg("force"):
                log_warning(
                    "Enforcing `--inc {}` although `max_increment` option is set to '{}'".format(
                        cli_arg("inc"), max_increment
                    )
                )
            else:
                return (
                    "`--inc {}` was passed, but the `max_increment` option is set to '{}'"
                    " (pass `--force` to ignore).".format(cli_arg("inc"), max_increment)
                )
        return True

    def run(self, context: TaskContext):
        opts = self.opts
        dry_run = context.dry_run

        if self.cli_arg("no_bump"):
            log_warning("`--no-bump` was passed: forcing dry-run mode for 'bump' task.")
            dry_run = True

        self.version_before_bump = context.version
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

        vm = context.version_manager
        repo = context.repo_obj

        org_version = context.org_version
        is_prerelease = bool(org_version and org_version.prerelease)
        tag_names = [tag.name.lstrip("vV") for tag in repo.tags]
        is_version_tagged = str(org_version).lstrip("vV") in tag_names

        if (
            self.cli_arg("inc") == "postrelease"
            and not opts.get("inc")
            and is_prerelease
        ):
            # If `--inc postrelease` was passed and the bump-task does not
            # explicitly define `inc: postrelease`, untagged releases are
            # not bumped again.
            if is_version_tagged:
                log_info(
                    f"Bump `--inc postrelease` is applied for TAGGED pre release {org_version}."
                )
            elif self.cli_arg("force_pre_bump"):
                log_warning(
                    f"Bump `--inc postrelease` was used for UNTAGGED pre release {org_version}. "
                    "`--force-pre-bump` is set: bumping anyway..."
                )
            else:
                log_warning(
                    "Bump `--inc postrelease` is ignored, because current version "
                    f"{org_version} is already a pre-release and not yet tagged "
                    f"(assuming the following tasks will tag and release {org_version}).\n"
                    "Pass `--force-pre-bump` to bump anyway."
                )
                return SkipTaskResult("Ignored for untagged pre-relase.")

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
