# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

from git import Repo

from .cmd_common import WorkflowTask
from .util import check_arg, log_dry, log_response


class CommitTask(WorkflowTask):
    DEFAULT_OPTS = {
        "add": [],  # Also `git add` these files ('.' for all)
        "add_known": True,  # Commit with -a flag
        "message": "Bumping version to {version}",
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["add"], (list, tuple))
        check_arg(opts["add_known"], bool)
        check_arg(opts["message"], str)

    def to_str(self, context):
        opts = self.opts
        add = opts["add"] or opts["add_known"]
        message = opts["message"].format(**vars(context))
        return "{}(add: {}, '{}')".format(self.__class__.__name__, add, message.strip())

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""
        sp = subparsers.add_parser(
            "commit",
            parents=parents,
            help="increment current 'patch' version (add `--minor` or `--major`)",
        )
        sp.add_argument(
            "--add-known", action="store_true", help="",
        )
        sp.set_defaults(command=cls.handle_cli_command)

    @classmethod
    def check_task_def(cls, task_def, parser, args, yaml):
        return True

    def run(self, context):
        opts = self.opts
        message = opts["message"].format(**vars(context))

        repo_path = os.path.abspath(".")
        repo = Repo(repo_path)
        git = repo.git
        # remote = repo.remote()
        index = repo.index

        opts_add = opts["add"]
        opts_add_known = opts["add_known"]

        if opts_add:
            check_arg(opts_add, (list, tuple))
            index.add(opts_add, write=not self.dry_run)

        if opts_add_known:
            res = git.add(".", dry_run=self.dry_run, verbose=self.verbose >= 4)
            log_response("git add .", res, "debug", self.dry_run)

        if self.dry_run:
            log_dry("commit")
        else:
            # if opts["add_known"]:
            index.commit(message,)
        return True
