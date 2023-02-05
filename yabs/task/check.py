# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import json
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from github import Github
from semantic_version import SimpleSpec, Version

from ..util import check_arg, log_debug, log_error, log_info, log_warning
from ..util import plural_s as ps
from ..util import to_list, write
from .common import (
    DEFAULT_USER_AGENT,
    REQUESTS_HEADERS,
    TaskContext,
    WarningTaskResult,
    WorkflowTask,
)

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


def _get_package_version(package_name, *, or_none=False):
    try:
        import importlib.metadata

        version = importlib.metadata.version(package_name)
    except ImportError:
        import pkg_resources

        version = pkg_resources.get_distribution(package_name).version

    # PEP 440 uses `1.2.3a1`, but semver demands `1.2.3-a1`
    match = re.match(
        r"^(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)(?P<suffix>.*)?",
        version,
    )
    version = "{}.{}.{}".format(
        match.group("major"), match.group("minor"), match.group("patch")
    )
    suffix = match.group("suffix")
    if suffix:
        version += "-" + suffix.lstrip("-.")
    return Version(version.strip())


class CheckTask(WorkflowTask):
    DEFAULT_OPTS = {
        "build": True,
        "can_push": True,
        "clean": True,
        "github": True,
        "os": None,
        "pypi": True,
        "python": None,
        "up_to_date": True,
        "venv": True,
        "version": True,
        "winget": None,  # default True if winget_relase task exists
        "yabs": None,
    }
    MANDATORY_OPTS = None

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts

        check_arg(opts["build"], bool, or_none=True)
        check_arg(opts["can_push"], bool, or_none=True)
        check_arg(opts["clean"], bool, or_none=True)
        # check_arg(opts["gh_auth"], dict, or_none=True)
        check_arg(opts["os"], (str, list, tuple), or_none=True)
        check_arg(opts["pypi"], bool, or_none=True)
        check_arg(opts["python"], (str, SimpleSpec), or_none=True)
        check_arg(opts["up_to_date"], bool, or_none=True)
        check_arg(opts["venv"], bool, or_none=True)
        check_arg(opts["winget"], bool, or_none=True)
        check_arg(opts["yabs"], (str, SimpleSpec), or_none=True)

        opts["os"] = to_list(opts["os"])
        if isinstance(opts["python"], str):
            opts["python"] = SimpleSpec(opts["python"])
        if isinstance(opts["yabs"], str):
            opts["yabs"] = SimpleSpec(opts["yabs"])

        if opts["winget"] is None:
            if task_inst.task_runner.get_first_task_instance(
                "winget_release"
            ) and not self.cli_arg("no_winget_release"):
                opts["winget"] = True
                log_debug(
                    "Assuming `check.winget: true`, because `winget_release` task is active."
                )
            else:
                log_debug(
                    "Assuming `check.winget: false`, because no `winget_release` task is active."
                )

        self.enabled_checks = [k for k, v in sorted(self.opts.items()) if v]
        self.run_checks = set()
        self.failed_checks = set()

    def to_str(self, context: TaskContext):
        # passed_tests = self.run_tests.difference(self.failed_tests)
        failed = ""
        if self.failed_checks:
            failed = ", ".join(sorted(self.failed_checks))
            failed = f", {len(self.failed_checks)} failed: {failed}"

        return (
            f"{self.__class__.__name__}("
            f"{len(self.run_checks)}/{len(self.DEFAULT_OPTS)} checks{failed})"
        )

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        # Additional arguments for the 'run' command
        run_parser.add_argument(
            "--no-check",
            action="store_true",
            help="don't let the 'check' task stop the workflow (log warnings instead)",
        )

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        return True

    def run(self, context: TaskContext):
        opts = self.opts
        cli_arg = self.cli_arg

        FLAG_ERROR = 1024
        FLAG_UP_TO_DATE = 512

        def _ok(name, msg, output=None):
            assert name in self.DEFAULT_OPTS
            self.run_checks.add(name)
            write(msg, level="info", prefix="check", output=output)

        def _warn(name, msg, output=None):
            assert name in self.DEFAULT_OPTS
            self.run_checks.add(name)
            write(msg, level="warning", prefix="check", output=output)

        def _error(name, msg, output=None):
            assert name in self.DEFAULT_OPTS
            self.run_checks.add(name)
            self.failed_checks.add(name)
            write(msg, level="error", prefix="check", output=output)
            err_list.append(msg)

        repo = context.repo_obj
        repo_remote = repo.remote()
        repo_name = opts.get("repo") or context.repo

        err_list = []

        if opts["build"]:
            dist_dir = Path("dist").absolute()
            if dist_dir.is_dir():
                _ok("build", f"Dist folder exists: {dist_dir}")
            else:
                _error(
                    "build",
                    f"Dist folder missing: {dist_dir}: Please create and add to .gitignore",
                )

        # if opts["branches"]:
        #     cur_branch = repo.active_branch.name
        #     if cur_branch in opts["branches"]:
        #         _ok(
        #             "branches",
        #             "Active branch {!r} is in allowed list ({}).".format(
        #                 cur_branch, ", ".join(opts["branches"])
        #             ),
        #         )
        #     else:
        #         _error(
        #             "branches",
        #             "Active branch {!r} not in allowed list ({}).".format(
        #                 cur_branch, ", ".join(opts["branches"])
        #             ),
        #         )

        if opts["can_push"]:
            try:
                info = repo_remote.push(dry_run=True)[0]
                if info.flags & FLAG_ERROR:
                    msg = f"`git push` would fail (flags: {info.flags})"
                    _error("can_push", msg, info.summary)
                elif not (info.flags & FLAG_UP_TO_DATE):
                    msg = f"`git push` would transfer data (flags: {info.flags})"
                    _warn("can_push", msg, info.summary)
                else:
                    _ok("can_push", "`git push` would succeed.")
            except Exception as e:
                _error("can_push", f"`git push` would fail: ({e})")

        if opts["clean"]:
            if repo.is_dirty():
                msg = "Repository has pending commits"
                _error("clean", msg, repo.git.status())
            else:
                _ok("clean", "Repository is clean.")

        if opts["github"]:
            if not repo_name or "/" not in repo_name:
                _error(
                    "github",
                    f"Invalid repo name (expected `GH-USER/PROJECT`): {repo_name}",
                )
            token = context.gh_auth_token
            try:
                gh = Github(token, user_agent=DEFAULT_USER_AGENT)
                gh_repo = gh.get_repo(repo_name, lazy=False)
                full_name = gh_repo.full_name
                _ok(
                    "github",
                    f"GitHub repo {repo_name} is accessible: {full_name}",
                )
            except Exception as e:
                _error("github", f"Could not access GitHub repo {repo_name}: {e!r}")

        if opts["os"]:
            system = platform.system()
            if system in opts["os"]:
                _ok(
                    "os",
                    "Platform {!r} is in allowed list ({}).".format(
                        system, ", ".join(opts["os"])
                    ),
                )
            else:
                _error(
                    "os",
                    "Platform {!r} not in allowed list ({}).".format(
                        system, ", ".join(opts["os"])
                    ),
                )

        if opts["python"]:
            req_ver = opts["python"]
            cur_ver = Version(".".join(map(str, sys.version_info[:3])))
            if req_ver.match(cur_ver):
                _ok("python", f"Python version {cur_ver} matches '{req_ver}'.")
            else:
                _error(
                    "python", f"Python version {cur_ver} does not match '{req_ver}'."
                )

        if opts["pypi"]:
            err = self._check_twine_availability()
            if err:
                _error("pypi", err)
            _ok("pypi", "`twine` is available and configured.")

            package_name = context.repo_short  # TODO: allow to override
            pypy_api_url = f"https://pypi.org/pypi/{package_name}/json"
            try:
                resp = None
                resp = requests.get(
                    pypy_api_url, verify=False, headers=REQUESTS_HEADERS
                )
                resp.raise_for_status()

                pypi_info = json.loads(resp.text)
                pypi_info = pypi_info["info"]
                _ok(
                    "pypi",
                    f"Package `{package_name}` is registered on PyPI "
                    f"(name: '{pypi_info['name']}', version: '{pypi_info['version']}').",
                )
            except Exception as e:
                if isinstance(e, requests.HTTPError) and resp.status_code == 404:
                    # https://packaging.python.org/en/latest/guides/migrating-to-pypi-org/#registering-package-names-metadata
                    _error(
                        "pypi",
                        f"Package `{package_name}` not yet registered on PyPI: "
                        "Continuing would register the new package.",
                    )
                    log_warning(
                        "This is not an error, just a warning to prevent accidental registration:"
                    )
                    log_warning(
                        "Ignore checks using `--no-checks` or run `twine upload` manually."
                    )
                else:
                    _error(
                        "pypi",
                        f"Failed to query package `{package_name}` on PyPI: {e!r}",
                    )

        if opts["up_to_date"]:
            try:
                status = None
                repo_remote.update()
                status = repo.git.status("-uno", porcelain=False)
                if 'use "git pull"' in status:
                    msg = "Remote branch contains unpulled changes"
                    _error("up_to_date", msg, status)
                else:
                    _ok("up_to_date", "Remote branch has not diverged.")
            except Exception as e:
                _error("up_to_date", f"Repo update & status failed: {e}")

        if opts["venv"]:
            is_venv = hasattr(sys, "real_prefix") or sys.base_prefix != sys.prefix
            if is_venv:
                _ok("venv", "Running inside a virtual environment.")
            else:
                _error("venv", "Not running inside a virtual environment.")

        if opts["version"]:
            # _ret_code, real_version = self._exec(
            #     ["python", "setup.py", "--version"], quiet=True
            # )
            setup_info = self.get_setup_metadata([])
            real_version = setup_info["version"]
            vm = context.version_manager
            if real_version != str(vm.master_version):
                _error(
                    "version",
                    "`setup.py --version` returned {real_version!r} (expected {vm.master_version!r}).",
                )
            else:
                _ok("version", f"`setup.py --version` returned {real_version!r}.")

        if opts["winget"]:
            winget_ok = True
            if platform.system() == "Windows":
                _ok("winget", "Running on MS Windows.")
            else:
                winget_ok = False
                _error(
                    "winget",
                    f"Runinng on {platform.system()} (winget needs MS Windows).",
                )

            if cli_arg("inc") == "postrelease":
                _error(
                    "winget",
                    "`--inc postrelease` not allowed (cannot publish pre-releases on winget-pkgs).",
                )

            if shutil.which("winget") and shutil.which("wingetcreate"):
                _ok("winget", "`winget` and `wingetcreate` are available.")
            else:
                winget_ok = False
                _error("winget", "`winget` and/or `wingetcreate` not available.")

            if winget_ok:
                # Is project is registered at winget-pkgs?
                package_name = context.repo_short  # TODO: allow to override
                ret_code, real_version = self._exec(
                    ["winget", "show", package_name], quiet=True
                )
                if ret_code:
                    if cli_arg("no_winget_release"):
                        _warn(
                            "winget",
                            f"Package `{package_name}` not found on winget-pkgs "
                            "(ignored, because --no-winget-release was passed).",
                        )
                    elif ret_code == 0x8A150014:
                        _error(
                            "winget",
                            f"Package `{package_name}` not yet registered on winget-pkgs: "
                            "Yabs supports updating existing packages only.",
                        )
                        log_warning(
                            f"winget returned code 0x{ret_code:08x}, "
                            "see https://github.com/microsoft/winget-cli/blob/master/src/AppInstallerCommonCore/Public/AppInstallerErrors.h"
                        )
                        log_warning(
                            "Note that Yabs only supports updating existing winget packages."
                        )
                        log_warning("Run `wingetcreate new` manually.")
                    else:
                        _error(
                            "winget",
                            f"Could not find package `{package_name}` on winget-pkgs "
                            f"(return code: 0x{ret_code:08x}): "
                            "Yabs supports updating existing packages only.",
                        )
                else:
                    _ok(
                        "winget",
                        f"Package `{package_name}` is registered on winget-pkgs.",
                    )

        if opts["yabs"]:
            req_ver = opts["yabs"]
            cur_ver = _get_package_version("yabs")
            if req_ver.match(cur_ver):
                _ok("yabs", f"Yabs version {cur_ver} matches '{req_ver}'.")
            else:
                _error("yabs", f"Yabs version {cur_ver} does not match '{req_ver}'.")

        log_info("")

        if err_list:
            log_error(
                f"{len(err_list)} test{ps(err_list)} failed "
                f"in {len(self.run_checks)} check{ps(self.run_checks)}:"
            )
            for msg in err_list:
                write(msg, level="error", prefix="check")

            if cli_arg("no_check"):
                msg = "`--no-check` was passed: ignoring the errors above."
                log_warning(msg)
                return WarningTaskResult(msg)
            else:
                log_info("Use the `--no-check` argument to ignore the errors above.")
                return False
        return True
