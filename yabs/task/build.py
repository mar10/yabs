# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pathlib import Path
from typing import TYPE_CHECKING

from ..util import (
    ConfigError,
    FolderContentMonitor,
    check_arg,
    log_debug,
    log_error,
    log_info,
    log_warning,
)
from .common import TaskContext, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class BuildTask(WorkflowTask):
    DEFAULT_OPTS = {
        "clean": True,
        "revert_bump_on_error": True,
        "targets": ["sdist", "bdist_wheel"],
    }
    MANDATORY_OPTS = None

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["clean"], bool)
        check_arg(opts["revert_bump_on_error"], bool)
        check_arg(opts["targets"], list)

        unknown = set(opts["targets"]).difference(self.KNOWN_TARGETS)
        if unknown:
            raise ConfigError(
                "Unkown `pypi_release.targets` value: {}".format(", ".join(unknown))
            )

    def to_str(self, context: TaskContext):
        opts = self.opts
        args = "{}".format(", ".join(opts["targets"]))
        return "{}(targets {})".format(self.__class__.__name__, args)

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    def _run(self, context: TaskContext):
        opts = self.opts
        ok = True

        extra_args = []
        # NOTE: `--dry-run` flag does not work well with setup.py?
        #    Seems to produce errors like
        #    "error: [Errno 2] No such file or directory: 'test-release-tool-0.0.1/PKG-INFO'"
        # if self.dry_run:
        #     extra_args.append("--dry-run")

        if self.verbose >= 4:
            extra_args.append("--verbose")
        elif self.verbose <= 2:
            extra_args.append("--quiet")

        # Check if setup.py really uses the expected name & version
        setup_info = self.get_setup_metadata(extra_args)
        real_name = setup_info["name"]
        real_version = setup_info["version"]
        # ret_code, real_version = self._exec(
        # ret_code, real_name = self._exec(["python", "setup.py", "--name"] + extra_args)
        # ret_code, real_version = self._exec(
        #     ["python", "setup.py", "--version"] + extra_args
        # )
        if real_version != str(context.version):
            if not self.dry_run:
                raise RuntimeError(
                    f"`setup.py --version` returned {real_version!r} (expected {context.version!r})"
                )

        targets = self.opts["targets"]
        dist_dir = Path("dist").absolute()

        matches = {}
        if "sdist" in targets:
            matches["sdist"] = r".*\.tar\.gz"
        if "bdist_wheel" in targets:
            matches["bdist_wheel"] = r".*\.whl"
        if "bdist_msi" in targets:
            raise RuntimeError("Define a separate 'exec' task' to create MSIs")

        artifacts_def = {
            "folder": dist_dir,
            "matches": matches,
        }
        ok = True
        with FolderContentMonitor(artifacts_def) as fcm:
            for target in targets:
                log_info(f"Building {target} for {real_name} {real_version}...")
                ret_code, _out = self._exec(
                    ["python", "setup.py", target, "--dist-dir", str(dist_dir)]
                    + extra_args
                )
                if ret_code != 0:
                    ok = False

        if fcm.changed_or_added_files:
            # log_info(f"Created artifacts: {fcm.changed_or_added_files}")
            log_info(f"Created artifacts: {fcm.changed_or_added_by_tag}")
            context.artifacts.update(fcm.changed_or_added_by_tag)
        elif artifacts_def and len(artifacts_def.get("matches", [])) != len(
            fcm.changed_or_added_files
        ):
            log_warning(
                f"No or not all artifacts created for `add_artifacts: {artifacts_def}`"
            )
        log_debug(f"Available artifacts: {context.artifacts}")

        if opts["clean"]:
            ret_code, _out = self._exec(
                ["python", "setup.py", "clean", "--all"] + extra_args
            )
            ok = ok and (ret_code == 0)

        return ok

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        return True

    def run(self, context: TaskContext):
        try:
            res = self._run(context)
            if res:
                return res
        except Exception as e:
            log_error("{}".format(e))

        if self.opts["revert_bump_on_error"] and not self.dry_run:
            # log_warning("Reverting bump {} => {} ...".format(vm.master_version, context.version))
            vm = context.version_manager
            vm.reset_version(write=not self.dry_run)
            context.version = vm.master_version

        return False
