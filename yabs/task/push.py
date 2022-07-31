# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from typing import TYPE_CHECKING

from git import Repo
from git.exc import GitCommandError

from ..util import check_arg, log_response
from .common import TaskContext, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class PushTask(WorkflowTask):
    DEFAULT_OPTS = {
        "target": "",  # E.g. 'upstream'
        "tags": False,  # Also push tags
    }
    MANDATORY_OPTS = None

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["target"], str)
        check_arg(opts["tags"], bool)

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
        target = self.opts["target"]
        repo_path = os.path.abspath(".")
        repo = Repo(repo_path)
        git = repo.git

        try:
            if target:
                res = git.push(
                    opts["target"],
                    follow_tags=opts["tags"],
                    dry_run=self.dry_run,
                    verbose=self.verbose >= 4,
                )
            else:
                res = git.push(
                    follow_tags=opts["tags"],
                    dry_run=self.dry_run,
                    verbose=self.verbose >= 4,
                )
            log_response("git push", res, "info", self.dry_run)
        except GitCommandError as e:
            log_response("git push", "{}".format(e), "error", self.dry_run)
            return False
        return True
