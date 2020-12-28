# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
import subprocess
import sys
from abc import ABC, abstractclassmethod, abstractmethod

from git import Repo

from .util import check_arg, log_warning, write

GH_USER_AGENT = "Yabs/Python"


class TaskContext:
    """
    Context information that is passed by the task runner to all tasks.
    This instance is used by tasks to pass information to downstream
    tasks.
    """

    def __init__(self, args, task_runner):
        self.errors = []
        self.completed = []
        #: CLI arguments namespace object
        self.args = args
        #: (str) value of ``--inc`` argument
        #: ('major', 'minor', 'patch', 'postrelease')
        self.inc = args.inc
        #: (bool) true if ``--dry-run`` was passed
        self.dry_run = args.dry_run
        #: (str) the repo's latest tag name (before 'bump')
        self.org_tag_name = None
        #: (str) the current tag name (after 'bump')
        self.tag_name = None
        #: (dict) all files that 'pypi_release' created, e.g.
        #: ``{"sdist": <path>, "bdist_msi": <path>}``
        self.artifacts = {}
        #: (:class:`~yabs.task_runner.TaskRunner`)
        self.task_runner = task_runner
        #: (str) GitHub repo name, e.g. 'USER/PROJECT'
        self.repo = None
        #: (str) Root folder
        self.repo_path = None
        #: (:class:`git.repo.base.Repo`)
        self.repo_obj = None
        #: (str) GitHub authentication token
        self.gh_auth_token = None
        #: (:class:`semantic_version.Version`) latest version (before 'bump')
        self.org_version = None
        #: (:class:`semantic_version.Version`) current version (after 'bump')
        self.version = None
        #: (:class:`~yabs.version_manager.VersionManager`)
        self.version_manager = None

        self.initialize()
        return

    def as_dict(self):
        return vars(self)

    def initialize(self):

        if self.task_runner:
            tr = self.task_runner
            self.repo = tr.get("repo")
            self.version_manager = tr.version_manager
            self.version = self.version_manager.master_version
            self.org_version = self.version
            auth = tr.get("gh_auth")
            if isinstance(auth, str):
                self.gh_auth_token = auth
            else:  # must be a dict
                self.gh_auth_token = os.environ.get(auth["oauth_token_var"])
        else:
            self.repo_path = os.path.abspath(".")

        repo = Repo(self.repo_path)
        self.repo_obj = repo

        try:
            repo.remote().fetch(tags=True)
        except Exception as e:
            log_warning("Unable to fetch tags from git remote: {}".format(e))

        try:
            # Test if we have tags (but this is not neccessarily the latest)
            has_tags = False
            tag = repo.tags[0]
            has_tags = True
            # log_info("Latest repo tag: {}".format(tag))
        except IndexError:
            pass

        if not has_tags:
            tag = "v0.0.0"
            log_warning(
                "Repository does not seem to have tags; assuming {}".format(tag)
            )
        else:
            res = repo.git.rev_list(tags=True, max_count=1)
            tag = repo.git.describe(res, tags=True)

        self.org_tag_name = tag


class WorkflowTask(ABC):
    """
    Common base class for all yabs tasks.
    """

    KNOWN_TARGETS = frozenset(("sdist", "bdist_wheel", "bdist_msi"))

    _COMMON_OPTS = frozenset(("dry_run", "verbose"))
    #: (dict) define all supported arguments and their default values.
    #: This attribute must be defined by derived classes.
    DEFAULT_OPTS = None

    def __init__(self, opts):
        assert self.DEFAULT_OPTS is not None
        # assert self.CLI_COMMAND is not None
        #: (dict) The actual arguments, i.e. the default values merged with
        #: passed options
        self.opts = self.DEFAULT_OPTS.copy()
        self.opts.update(opts)
        check_arg(self.opts.get("dry_run"), bool)
        check_arg(self.opts.get("verbose"), int)
        #: (bool) true if `--dry-run` was passed to the CLI
        self.dry_run = self.opts.get("dry_run")
        #: (int, default=3) 0..5
        self.verbose = self.opts.get("verbose")
        known_opts = set(self.DEFAULT_OPTS).union(self._COMMON_OPTS)
        unknown_opts = set(opts.keys()).difference(known_opts)
        if unknown_opts:
            log_warning(
                "{}(): passed unknown option(s): {}".format(
                    self, ", ".join(unknown_opts)
                )
            )

    def __str__(self):
        return self.to_str({})

    def to_str(self, context):
        return "{}()".format(self.__class__.__name__)

    def _exec(self, args, quiet=None):
        """
        Args:
            args (list): array of string values that define the command line

        Returns:
            tuple (ret_code, output)
        """
        opts = self.opts

        # Fix python calls to use the executable from the virtual environment
        if args[0].lower() == "python":
            args[0] = sys.executable

        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        ret_code = res.returncode
        output = res.stdout.decode().strip()
        msg = "`{}` returned code {}".format(" ".join(args), ret_code)

        if ret_code != 0:
            if opts.get("ignore_errors"):
                write(msg, "warning", True, output)
                return True, None
            write(msg, "error", True, output)
        elif quiet is not True and not opts.get("silent"):
            write(msg, "debug", True, output)
        return ret_code, output

    @abstractclassmethod
    def check_task_def(cls, task_def, parser, args, yaml):  # noqa: B902 'use cls'
        """Check task definition for errors.

        This allows static pre-checks before the actual workflow starts.

        Returns:
            (str|list|bool) Error message(s)
        """
        return True

    @classmethod
    def handle_cli_command(cls, parser, args):
        """Default implementation, when run as stand-alone CLI command."""
        # Convert args namespace to option dict items:
        opts = vars(args)
        # Create task instance
        task = cls(opts)
        # The TaskRunner would maintain a `context` dict, when running a
        # sequence of workflow tasks. Here we need to set-up a simple one:
        context = TaskContext(args, None)
        res = task.run(context=context)
        return res

    @abstractclassmethod
    def register_cli_command(cls, subparsers, parents, run_parser):  # noqa: B902
        """Let tasks add a sub-command and/or arguments to the 'run' command."""

    @abstractmethod
    def run(self, context):
        """"""
