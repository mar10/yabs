# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import platform
import shutil
import sys

from github import Github
from semantic_version import SimpleSpec, Version

from .cmd_common import WorkflowTask, GH_USER_AGENT

from .util import (
    check_arg,
    log_info,
    log_warning,
    to_list,
    write,
)


class CheckTask(WorkflowTask):
    DEFAULT_OPTS = {
        "branches": None,
        "can_push": None,
        "clean": None,
        # "cmp_version": None,
        # "connected": None,
        # "gh_auth": None,  # use `config.gh_auth`
        "github": None,
        "os": None,
        "python": None,
        "twine": None,
        "up_to_date": None,
        "venv": None,
        "version": None,
    }

    def __init__(self, config):
        super().__init__(config)
        opts = self.opts

        check_arg(opts["branches"], (str, list, tuple), or_none=True)
        check_arg(opts["can_push"], bool, or_none=True)
        check_arg(opts["clean"], bool, or_none=True)
        check_arg(opts["os"], (str, list, tuple), or_none=True)
        check_arg(opts["python"], (str, SimpleSpec), or_none=True)
        check_arg(opts["twine"], bool, or_none=True)
        check_arg(opts["up_to_date"], bool, or_none=True)
        check_arg(opts["venv"], bool, or_none=True)
        # check_arg(opts["gh_auth"], dict, or_none=True)

        opts["branches"] = to_list(opts["branches"])
        opts["os"] = to_list(opts["os"])
        if isinstance(opts["python"], str):
            opts["python"] = SimpleSpec(opts["python"])

    def to_str(self, context):
        checks = ", ".join([k for k, v in sorted(self.opts.items()) if v])
        return "{}({})".format(self.__class__.__name__, checks)

    @classmethod
    def register_cli_command(cls, subparsers, parents):
        """"""
        sp = subparsers.add_parser(
            "check", parents=parents, help="check preconditions",
        )

        sp.add_argument(
            "--branch",
            nargs="*",
            metavar="BRANCH",
            dest="branches",
            help="check if current branch is allowed",
        )
        sp.add_argument(
            "--can-push", action="store_true", help="assert `git push` would work",
        )
        sp.add_argument(
            "--venv",
            action="store_true",
            help="assert running inside a virtual environment",
        )
        sp.add_argument(
            "--github", action="store_true", help="assert gitub repo is available",
        )
        sp.add_argument(
            "--twine", action="store_true", help="assert twine is available",
        )
        sp.add_argument(
            "--clean",
            action="store_true",
            help="assert that all changes are committed",
        )
        sp.add_argument(
            "--os",
            choices=["Linux", "Darwin", "Windows"],
            nargs="*",
            help="check current operating system",
        )
        sp.set_defaults(command=cls.handle_cli_command)

    def run(self, context):
        opts = self.opts
        FLAG_ERROR = 1024
        FLAG_UP_TO_DATE = 512

        err_list = []

        def _ok(msg, output=None):
            write(msg, "info", "check", output)

        def _error(msg, output=None):
            write(msg, "error", "check", output)
            err_list.append(msg)

        def _warn(msg, output=None):
            write(msg, "warning", "check", output)

        # project_info = get_project_info()
        # print(project_info)

        repo = context.repo_obj
        remote = repo.remote()

        # dist = pkg_resources.get_distribution("yabs")
        # assert dist.version == __version__
        # print(opts)
        if opts["branches"]:
            cur_branch = repo.active_branch.name
            if cur_branch in opts["branches"]:
                _ok(
                    "Active branch {!r} is in allowed list ({}).".format(
                        cur_branch, ", ".join(opts["branches"])
                    )
                )
            else:
                _error(
                    "Active branch {!r} not in allowed list ({}).".format(
                        cur_branch, ", ".join(opts["branches"])
                    )
                )

        if opts["can_push"]:
            info = remote.push(dry_run=True)[0]

            if info.flags & FLAG_ERROR:
                msg = "`git push` would fail (flags: {})".format(info.flags)
                _error(msg, info.summary)
            elif not (info.flags & FLAG_UP_TO_DATE):
                msg = "`git push` would transfer data (flags: {})".format(info.flags)
                _warn(msg, info.summary)
            else:
                _ok("`git push` would succeed.")

        # if opts["cmp_version"]:
        #     raise NotImplementedError

        # if opts["connected"]:
        #     raise NotImplementedError

        if opts["clean"]:
            if repo.is_dirty():
                msg = "Repository has pending commits"
                _error(msg, repo.git.status())
            else:
                _ok("Repository is clean.")

        if opts["github"]:
            repo_name = opts.get("repo") or context.repo
            if not repo_name or "/" not in repo_name:
                _error(
                    "Invalid repo name (expected `GH-USER/PROJECT`): {}".format(
                        repo_name
                    )
                )
            token = context.gh_auth_token
            try:
                gh = Github(token, user_agent=GH_USER_AGENT)
                gh_repo = gh.get_repo(repo_name, lazy=False)
                full_name = gh_repo.full_name
                _ok("GitHub repo {} is accessible: {}".format(repo_name, full_name))
            except Exception as e:
                _error("Could not access GitHub repo {}: {}".format(repo_name, e))

        if opts["os"]:
            info = remote.push(dry_run=True)[0]
            # print("push", info.flags, info.summary)
            ps = platform.system()
            if ps in opts["os"]:
                _ok(
                    "Platform {!r} is in allowed list ({}).".format(
                        ps, ", ".join(opts["os"])
                    )
                )
            else:
                _error(
                    "Platform {!r} not in allowed list ({}).".format(
                        ps, ", ".join(opts["os"])
                    )
                )

        if opts["python"]:
            py_ver = Version(".".join(map(str, sys.version_info[:3])))
            if opts["python"].match(py_ver):
                _ok("Python version {} matches {}.".format(py_ver, opts["python"]))
            else:
                _error(
                    "Python version {} does not match {}.".format(
                        py_ver, opts["python"]
                    )
                )

        if opts["twine"]:
            if shutil.which("twine"):
                _ok("`twine` is available.")
            else:
                _error("`twine` not available.")

        if opts["up_to_date"]:
            remote.update()
            status = repo.git.status("-uno", porcelain=False)
            if 'use "git pull"' in status:
                msg = "Remote branch contains unpulled changes"
                _error(msg, status)
            else:
                _ok("Remote branch has not diverged.")

        if opts["venv"]:
            is_venv = hasattr(sys, "real_prefix") or sys.base_prefix != sys.prefix
            if is_venv:
                _ok("Running inside a virtual environment.")
            else:
                _error("Not running inside a virtual environment.")

        if opts["version"]:
            _ret_code, real_version = self._exec(
                ["python", "setup.py", "--version"], quiet=True
            )
            vm = context.version_manager
            if real_version != str(vm.master_version):
                _error(
                    "`setup.py --version` returned {} (expected {}).".format(
                        real_version, vm.master_version
                    )
                )
            else:
                _ok("`setup.py --version` returned {}.".format(real_version))

        if err_list:
            write("Checks failed:\n  - {}".format("\n  - ".join(err_list)), "error")
            if context._args.no_check:
                log_warning("`--no-check` was passed: ignoring the errors above.")
            else:
                log_info("Use the `--no-check` argument to ignore the errors above.")
                return False
        return True
