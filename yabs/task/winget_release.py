# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from typing import TYPE_CHECKING

from github import Github

from ..util import ConfigError, check_arg, log_dry, log_error, log_warning
from .common import (
    DEFAULT_USER_AGENT,
    SkipTaskResult,
    TaskContext,
    WarningTaskResult,
    WorkflowTask,
)

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class WingetReleaseTask(WorkflowTask):
    DEFAULT_OPTS = {
        "gh_auth": None,  # use `config.gh_auth`
        "package_id": None,
        # "urls": "",
        "upload": None,  # "bdist_msi",
        "out": None,
    }
    MANDATORY_OPTS = {"package_id", "upload"}

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["gh_auth"], (dict, str), or_none=True)
        check_arg(opts["package_id"], str)
        check_arg(opts["upload"], str, opts["upload"] == "bdist_msi")

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
        is_prerelease = bool(cur_version and cur_version.prerelease)
        tag_names = [tag.name.lstrip("vV") for tag in context.repo_obj.tags]
        is_version_tagged = str(cur_version).lstrip("vV") in tag_names

        if is_prerelease:
            return WarningTaskResult(
                f"Cannot publish pre-releases to winget-pkgs: {cur_version}: skipping."
            )
        elif not is_version_tagged:
            return WarningTaskResult(
                f"Cannot publish untagged releases to winget-pkgs: {cur_version}: skipping."
            )

        ok = True

        # Check GH Token access
        gh = Github(context.gh_auth_token, user_agent=DEFAULT_USER_AGENT)
        try:
            repo = gh.get_repo(context.repo, lazy=False)
            if not repo:
                raise ConfigError(
                    f"Could not open repo '{context.repo}' with GitHub token."
                )
        except Exception as e:
            log_error(f"Could not open repo '{context.repo}' with GitHub token: {e!r}")
            return False

        # Check if artifact as created
        upload_target = opts["upload"]  # e.g. 'bdist_msi'
        upload_path = context.artifacts.get(upload_target)
        if not upload_path or not os.path.isfile(upload_path):
            log_warning(
                f"artifact does not exist (not created): {upload_target}: {upload_path}"
            )

        # self._exec(["wingetcreate", "submit", "-?"])

        # <a href="/mar10/stressor/releases/download/v0.5.1/stressor-0.5.1.0-amd64.msi" rel="nofollow" data-skip-pjax="">
        file_name = upload_path.name
        urls = (
            f"https://github.com/{context.repo}"
            f"/releases/download/v{context.version}/{file_name}"
        )
        args = [
            "wingetcreate",
            "update",
            # "--out",
            # "xxx",
            "--urls",
            urls,
            # "--version",
            # "xxx",
            "--token",
            "REDACTED" if self.dry_run else context.gh_auth_token,
            # "--submit",
            str(upload_path),
        ]

        if self.dry_run:
            msg = " ".join(args)
            log_dry(f"{msg}")
        else:
            args.extend([])
            ret_code, _out = self._exec(args)
            ok = ok and (ret_code == 0)

        char0 = context.repo[0]
        package_name = context.repo_short  # TODO: allow to override
        url = f"https://github.com/microsoft/winget-pkgs/tree/master/manifests/{char0}/{package_name}/{context.tag_name}"
        self.task_inst.task_runner.add_summary(
            f"Created Windows Package Manager release at {url}"
        )
        return ok
