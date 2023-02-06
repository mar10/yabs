# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from typing import TYPE_CHECKING

from ..util import check_arg, log_dry, log_warning
from .common import SkipTaskResult, TaskContext, WarningTaskResult, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class WingetReleaseTask(WorkflowTask):
    DEFAULT_OPTS = {
        "gh_auth": None,  # use `config.gh_auth`
        "out": "dist",
        "package_id": None,
        # "token": None,
        "upload": None,  # Must be "bdist_msi",
    }
    MANDATORY_OPTS = {"package_id", "upload"}

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["gh_auth"], (dict, str), or_none=True)
        check_arg(opts["package_id"], str)
        check_arg(opts["upload"], str, opts["upload"] == "bdist_msi")
        check_arg(opts["out"], str, or_none=True)

    # def to_str(self, context :TaskContext):
    #     add = self.opts["add"] or self.opts["add_known"]
    #     return "{}(add: {}, '{}')".format(
    #         self.__class__.__name__, add, self.opts["message"]
    #     )

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        run_parser.add_argument(
            "--no-winget-release",
            action="store_true",
            help="run all 'winget_release' tasks in dry-run mode",
        )

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        return True

    def run(self, context: TaskContext):
        opts = self.opts
        cli_arg = self.cli_arg

        if cli_arg("no_release"):
            return SkipTaskResult("`--no-release` was passed: skipping.")
        if cli_arg("no_winget_release"):
            return SkipTaskResult("`--no-winget-release` was passed: skipping.")

        cur_version = context.version
        assert "v" not in str(cur_version).lower()

        is_prerelease = bool(cur_version and cur_version.prerelease)
        tag_names = [tag.name.lstrip("vV") for tag in context.repo_obj.tags]
        is_version_tagged = str(cur_version) in tag_names

        if is_prerelease:
            return WarningTaskResult(
                f"Cannot publish pre-releases to winget-pkgs: {cur_version}: skipping."
            )
        elif not is_version_tagged:
            return WarningTaskResult(
                f"Cannot publish untagged releases to winget-pkgs: {cur_version}: skipping."
            )

        wpm_version = f"{cur_version}.0"

        ok = True

        # # Check GH Token access
        # gh = Github(context.gh_auth_token, user_agent=DEFAULT_USER_AGENT)
        # try:
        #     repo = gh.get_repo(context.repo, lazy=False)
        #     if not repo:
        #         raise ConfigError(
        #             f"Could not open repo '{context.repo}' with GitHub token."
        #         )
        # except Exception as e:
        #     log_error(f"Could not open repo '{context.repo}' with GitHub token: {e!r}")
        #     return False

        # Check if artifact is created
        # (no need to bail out, since `wingetcreate` will fail anyways)

        upload_target = opts["upload"]  # e.g. 'bdist_msi'
        upload_path = context.artifacts.get(upload_target)
        if not upload_path or not os.path.isfile(upload_path):
            log_warning(
                f"Artifact type '{upload_target}' does not exist (not created): {upload_path}\n"
                "Did you forget to add an `exec` task to build one?"
            )
        if wpm_version not in str(upload_path):
            log_warning(
                f"Artifact file name does not contain the expected version {wpm_version}: {upload_path}"
            )

        file_name = upload_path.name
        urls = (
            f"https://github.com/{context.repo}"
            f"/releases/download/v{context.version}/{file_name}"
        )
        package_id = opts["package_id"]
        out_folder = opts["out"]  # defaults to 'dist'

        args = [
            "wingetcreate",
            "update",
            "--urls",
            urls,  # Location of MSI asset in the GitHub release
            "--token",
            context.gh_auth_token,
            "--version",
            wpm_version,  # e.g. '1.2.3.0'
            "--out",
            out_folder,
            # Positional args:
            package_id,
        ]

        if self.dry_run:
            log_dry(
                f"Manifest file will be created in `{out_folder}/` (not submitted)!"
            )
        else:
            args.append("--submit")

        ret_code, _out = self._exec(args)
        if ret_code:
            log_warning(
                "If submit fails, it may be necessary to synchronize the repository.\n"
                + "See https://yabs.readthedocs.io/en/latest/ug_tutorial.html#windows-package-manager"
            )

        ok = ok and (ret_code == 0)

        char0 = context.repo[0]
        # package_name = context.repo_short  # TODO: allow to override
        url = f"https://github.com/microsoft/winget-pkgs/tree/master/manifests/{char0}/{package_id}/{wpm_version}"
        if ok and not self.dry_run:
            self.task_inst.task_runner.add_summary(
                f"Created Windows Package Manager release at {url}"
            )
        return ok
