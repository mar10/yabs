# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from typing import TYPE_CHECKING

from git import Repo
from git.exc import GitCommandError

from ..util import check_arg, log_dry, log_response
from .common import TaskContext, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class TagTask(WorkflowTask):
    DEFAULT_OPTS = {
        "name": "v{version}",
        "message": "Version {version}",
    }
    MANDATORY_OPTS = None

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["name"], str)
        check_arg(opts["message"], str)

    # def to_str(self, context :TaskContext):
    #     add = self.opts["add"] or self.opts["add_known"]
    #     return "{}(add: {}, '{}')".format(
    #         self.__class__.__name__, add, self.opts["message"]
    #     )

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        return True

    def run(self, context: TaskContext):
        opts = self.opts
        name = opts["name"].format(**vars(context))
        message = opts["message"].format(**vars(context))

        repo_path = os.path.abspath(".")
        repo = Repo(repo_path)
        git = repo.git

        if self.dry_run:
            log_dry("git tag -a {}".format(name))
            context.tag_name = name
            return True
        try:
            res = git.tag(
                name,
                annotate=True,
                message=message,
                dry_run=self.dry_run,
                verbose=self.verbose >= 4,
            )
            log_response("git tag {}".format(name), res, "info", self.dry_run)
            context.tag_name = name
        except GitCommandError as e:
            log_response("git tag", "{}".format(e), "error", self.dry_run)
            return False
        return True
