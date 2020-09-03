# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

from git import Repo
from git.exc import GitCommandError

from .cmd_common import WorkflowTask
from .util import check_arg, log_dry, log_response


class TagTask(WorkflowTask):
    DEFAULT_OPTS = {
        "name": "v{version}",
        "message": "Version {version}",
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["name"], str)
        check_arg(opts["message"], str)

    # def to_str(self, context):
    #     add = self.opts["add"] or self.opts["add_known"]
    #     return "{}(add: {}, '{}')".format(
    #         self.__class__.__name__, add, self.opts["message"]
    #     )

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    @classmethod
    def check_task_def(cls, task_def, parser, args, yaml):
        return True

    def run(self, context):
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
