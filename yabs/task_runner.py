# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
import time

import yaml

from snazzy import emoji

from .cmd_bump import BumpTask
from .cmd_check import CheckTask
from .cmd_commit import CommitTask
from .cmd_common import TaskContext
from .cmd_exec import ExecTask
from .cmd_gh_release import GithubReleaseTask
from .cmd_push import PushTask
from .cmd_pypi_release import PypiReleaseTask
from .cmd_tag import TagTask
from .plugin_manager import PluginManager
from .util import (
    NO_DEFAULT,
    ConfigError,
    check_arg,
    format_elap,
    log_debug,
    log_error,
    log_ok,
    log_warning,
    resolve_path,
)
from .version_manager import VersionFileManager


class TaskRunner:
    """"""

    # TODO: automate this map creation:
    handler_map = {
        "bump": BumpTask,
        "check": CheckTask,
        "commit": CommitTask,
        "exec": ExecTask,
        "github_release": GithubReleaseTask,
        "push": PushTask,
        "pypi_release": PypiReleaseTask,
        "tag": TagTask,
    }

    def __init__(self, fspec, parser=None, args=None):
        self.fspec = fspec
        self.parser = parser
        self.args = args
        self.all = None
        self.config = None
        self.tasks = None
        self.version_manager = None
        self.plugin_manager = PluginManager(self)
        self._load()
        self._check_config(parser, args)
        # register_command_handlers(self.handler_map)

    def get(self, key, default=NO_DEFAULT):
        try:
            return self.config[key]
        except KeyError:
            if default is NO_DEFAULT:
                raise
        return default

    def make_abs_path(self, key, default=None):
        return self.config.get(key, default)

    def _load(self):
        with open(self.fspec, "rt") as f:
            try:
                res = yaml.safe_load(f)
            except yaml.parser.ParserError as e:
                raise RuntimeError("Could not parse YAML: {}".format(e)) from None

        if not isinstance(res, dict) or not res.get("file_version", "").startswith(
            "yabs#"
        ):
            raise ConfigError("Not a `yabs` file (missing 'yabs#VERSION' tag).")
        self.all = res
        self.config = res["config"]
        check_arg(self.config, dict)
        self.tasks = res["tasks"]
        check_arg(self.tasks, list)

        self.version_manager = VersionFileManager(self)
        return

    def _check_config(self, parser, args):
        """Early option and command line syntax checks.

        This is done after reading the YAML and parsing the command line,
        but before the workflow starts.
        Note that `parser` and `args` may be None, when the TaskRunner was
        created by a srcipt (or test fixture).
        """
        errors = []

        for task_def in self.tasks:
            task_type = task_def["task"]
            task_cls = TaskRunner.handler_map.get(task_type)
            if task_cls is None:
                errors.append(
                    "Invalid task definition: '{}': {}".format(task_type, task_def)
                )
                continue
            res = task_cls.check_task_def(task_def, parser, args, self.all)
            if res in (None, True):
                continue
            if res is False:
                res = "{}({}): check failed.".format(task_cls, task_def)
            if isinstance(res, str):
                res = [res]
            check_arg(res, (list, tuple), or_none=True)
            errors.extend(res)

        if errors:
            raise ConfigError("ConfigError:\n  - {}".format("\n  - ".join(errors)))
        return True

    def run(self):
        context = TaskContext(self.args, self)
        ok = True
        start = time.monotonic()
        for task_def in self.tasks:
            task_def = task_def.copy()
            # log_info(task_def)
            task_type = task_def.pop("task")
            task_cls = TaskRunner.handler_map.get(task_type)
            if not task_cls:
                raise ConfigError(
                    "Invalid task type: {} (expected {})".format(
                        task_type, ", ".join(self.handler_map.keys())
                    )
                )
            # TODO: task_def can force - but not prevent - dry-run:
            task_def["dry_run"] = self.args.dry_run
            task_def["verbose"] = self.args.verbose
            task = task_cls(task_def)
            task_str = task.to_str(context)
            log_debug("Running {}: {}...".format(task_str, task.opts))
            res = task.run(context)
            task_str = task.to_str(context)  # __str__ may have changed
            if res:
                log_ok("{}".format(task_str))
            else:
                log_error("{}".format(task_str))
                context.errors.append(task_str)
                ok = False
                # if not args.force_continue:
                break

        elap = time.monotonic() - start
        if ok:
            log_ok(
                "Workflow finished successfully in {}{}".format(
                    format_elap(elap), emoji(" ✨ 🍰 ✨")
                )
            )
        else:
            msg = "Workflow failed in {}{}".format(format_elap(elap), emoji(" 💥 💔 💥"))
            log_error(msg)
            context.errors.append(msg)

        if self.args.dry_run:
            log_warning(
                "Dry-Run mode: No bits were harmed during the making of this release."
            )
        return ok

    # def find_project_root(self, fspec="."):
    #     """Return the nearest parent path that conatains setup.py."""
    #     path = Path(fspec).absolute()
    #     while path.parents:
    #         log_info("Searching {}...".format(path))
    #         if (path / "setup.py").is_file():
    #             return path
    #         path = path.parent
    #     return None


def handle_run_command(parser, args):
    fspec = resolve_path(os.getcwd(), args.workflow, must_exist=True)
    tm = TaskRunner(fspec, parser, args)
    res = tm.run()
    return res
