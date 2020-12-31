# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pathlib import Path

from .cmd_common import WorkflowTask
from .util import ConfigError, check_arg, log_dry, log_warning


def get_folder_file_names(folder):
    """Return folder files names as set."""
    p = Path(folder)
    name_set = set([e.name for e in p.iterdir()])
    return name_set


class PypiReleaseTask(WorkflowTask):
    DEFAULT_OPTS = {
        "upload": None,  # ["sdist", "bdist_wheel"],
        # "ignore_errors": False,
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["upload"], list, or_none=True)

        if opts["upload"] is not None:
            unknown = set(opts["upload"]).difference(self.KNOWN_TARGETS)
            if unknown:
                raise ConfigError(
                    "Unkown `pypi_release.upload` value: {}".format(", ".join(unknown))
                )
        return

    def to_str(self, context):
        opts = self.opts
        args = "{}".format(opts["upload"])
        return "{}({})".format(self.__class__.__name__, args)

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    def run(self, context):
        opts = self.opts
        ok = True

        extra_args = []

        if self.verbose >= 4:
            extra_args.append("--verbose")
        elif self.verbose <= 2:
            extra_args.append("--quiet")

        if context.args.no_release:
            log_warning(
                "`--no-release` was passed: skipping 'pypi_release' task (`twine upload`)."
            )
            return True

        # TODO: assert that all upload a are in context.artifacts
        upload = opts["upload"]
        for target, path in context.artifacts.items():
            if upload and target not in upload:
                continue

            if self.dry_run:
                log_dry("twine upload {}".format(path))
            else:
                # TODO: uses .pypirc
                ret_code, _out = self._exec(
                    [
                        "twine",
                        "upload",
                        "--non-interactive",
                        "--verbose",
                        # "--skip-existing",
                        "--disable-progress-bar",
                        str(path),
                    ]
                )
                ok = ok and (ret_code == 0)

        return ok

    @classmethod
    def check_task_def(cls, task_def, parser, args, yaml):
        return True
