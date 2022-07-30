# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from typing import TYPE_CHECKING

from ..util import ConfigError, check_arg, log_dry, log_info, log_warning
from .common import TaskContext, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class PypiReleaseTask(WorkflowTask):
    DEFAULT_OPTS = {
        "upload": None,  # ["sdist", "bdist_wheel"],
        "comment": None,
        # "ignore_errors": False,
    }
    MANDATORY_OPTS = None

    # PyPI does not accept MSI, etc.
    KNOWN_PYPI_TARGETS = frozenset(("sdist", "bdist_wheel"))

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["upload"], list, or_none=True)

        if opts["upload"] is not None:
            unknown = set(opts["upload"]).difference(self.KNOWN_PYPI_TARGETS)
            if unknown:
                raise ConfigError(
                    "Unkown `pypi_release.upload` value: {}".format(", ".join(unknown))
                )
        return

    def to_str(self, context: TaskContext):
        opts = self.opts
        args = "{}".format(opts["upload"])
        return f"{self.__class__.__name__}({args})"

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    def run(self, context: TaskContext):
        opts = self.opts
        cli_arg = self.cli_arg

        ok = True

        extra_args = []

        if self.verbose >= 4:
            extra_args.append("--verbose")
        elif self.verbose <= 2:
            extra_args.append("--quiet")

        if cli_arg("no_release"):
            log_warning(
                "`--no-release` was passed: skipping 'pypi_release' task (`twine upload`)."
            )
            return True

        # TODO:
        upload = opts["upload"]
        if upload is None:
            upload = self.KNOWN_PYPI_TARGETS

        for target, path in context.artifacts.items():
            if target not in upload:
                log_info(f"Skipping PyPI upload for unsupported distribution {path}")
                continue

            if self.dry_run:
                log_dry(f"twine upload {path}")
            else:
                args = [
                    "twine",
                    "upload",
                    "--non-interactive",
                    "--verbose",
                    # "--skip-existing",
                    "--disable-progress-bar",
                ]
                if opts["comment"]:
                    args.extend(["--comment", f"{opts['comment']}"])
                args.append(str(path))

                ret_code, _out = self._exec(args)
                ok = ok and (ret_code == 0)
        if ok and not self.dry_run:
            package_name = context.repo_short  # TODO: allow to override
            url = f"https://pypi.org/project/{package_name}/{context.tag_name}"
            self.task_inst.task_runner.add_summary(f"Created PyPI release at {url}")
        return ok

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        return True
