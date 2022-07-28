# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
import shutil
import subprocess
import sys
from abc import ABC, abstractclassmethod, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from git import Repo
from semantic_version import Version

from ..util import assert_always, check_arg, check_dict_keys, log_warning, write

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance, TaskRunner
    from yabs.version_manager import VersionFileManager


DEFAULT_USER_AGENT = "Yabs/Python"

REQUESTS_HEADERS = {"User-Agent": DEFAULT_USER_AGENT}


class TaskContext:
    """
    Context information that is passed by the task runner to all tasks.
    This instance is used by tasks to pass information to downstream
    tasks.
    """

    def __init__(self, task_runner):
        self.errors = []
        self.completed = []
        # #: CLI arguments namespace object
        # self.args = args
        #: (str) value of ``--inc`` argument
        #: ('major', 'minor', 'patch', 'postrelease')
        self.inc: str = task_runner.cli_arg("inc", None)
        #: (bool) true if ``--dry-run`` was passed
        self.dry_run: bool = task_runner.cli_arg("dry_run", None)
        #: (str) the repo's latest tag name (before 'bump')
        self.org_tag_name: str = None
        #: (str) the current tag name (after 'bump')
        self.tag_name: str = None
        #: (dict) all files that 'pypi_release' created, e.g.
        #: ``{"sdist": <path>, "bdist_msi": <path>}``
        self.artifacts: dict = {}
        #: (:class:`~yabs.task_runner.TaskRunner`)
        self.task_runner: TaskRunner = task_runner
        #: (str) GitHub repo name, e.g. 'USER/PROJECT'
        self.repo: str = None
        #: (str) Short repo name, without user/ prefixe.g. 'PROJECT'
        self.repo_short: str = None
        #: (str) Root folder
        self.repo_path: Path = None
        #: (:class:`git.repo.base.Repo`)
        self.repo_obj: Repo = None
        #: (str) GitHub authentication token
        self.gh_auth_token: str = None
        #: (:class:`semantic_version.Version`) latest version (before 'bump')
        self.org_version: Version = None
        #: (:class:`semantic_version.Version`) current version (after 'bump')
        self.version: Version = None
        #: (:class:`~yabs.version_manager.VersionManager`)
        self.version_manager: VersionFileManager = None

        self.initialize()
        return

    def as_dict(self):
        return vars(self)

    def initialize(self):

        if self.task_runner:
            tr = self.task_runner
            self.repo = tr.get_config("repo")
            self.repo_short = self.repo.split("/", 1)[1]
            git_repo = Repo(tr.fspec, search_parent_directories=True)
            self.version_manager = tr.version_manager
            self.version = self.version_manager.master_version
            self.org_version = self.version
            auth = tr.get_config("gh_auth")
            if isinstance(auth, str):
                self.gh_auth_token = auth
            else:  # must be a dict
                self.gh_auth_token = os.environ.get(auth["oauth_token_var"])
        else:
            git_repo = Repo(tr.fspec, search_parent_directories=True)
            # self.repo_path = os.path.abspath(".")

        self.repo_obj = git_repo
        self.repo_path = git_repo.common_dir

        try:
            git_repo.remote().fetch(tags=True)
        except Exception as e:
            log_warning(f"Unable to fetch tags from git remote: {e}")

        try:
            # Test if we have tags (but this is not neccessarily the latest)
            has_tags = False
            tag = git_repo.tags[0]
            has_tags = True
            # log_info("Latest repo tag: {}".format(tag))
        except IndexError:
            pass

        if not has_tags:
            tag = "v0.0.0"
            log_warning(f"Repository does not seem to have tags; assuming {tag}")
        else:
            res = git_repo.git.rev_list(tags=True, max_count=1)
            tag = git_repo.git.describe(res, tags=True)

        self.org_tag_name = tag


class _TaskResult:
    VALID_RESULTS = {"ok", "skip", "warning", "error"}

    def __init__(self, status, *, msg: str = None) -> None:
        check_arg(status, allowed_types=(str, bool))
        if status is True:
            status = "ok"
        elif status is False:
            status = "error"
        assert_always(status in _TaskResult.VALID_RESULTS)
        self.status = status
        self.message = msg

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.status})"


class OkTaskResult(_TaskResult):
    def __init__(self, msg: str = None) -> None:
        super().__init__("ok", msg=msg)


class SkipTaskResult(_TaskResult):
    def __init__(self, msg: str) -> None:
        super().__init__("skip", msg=msg)


class WarningTaskResult(_TaskResult):
    def __init__(self, msg: str) -> None:
        super().__init__("warning", msg=msg)


class ErrorTaskResult(_TaskResult):
    def __init__(self, msg: str) -> None:
        super().__init__("error", msg=msg)


class WorkflowTask(ABC):
    """
    Common base class for all yabs tasks.
    """

    #: (frozenset) Task options shared by all task
    KNOWN_TARGETS = frozenset(("sdist", "bdist_wheel", "bdist_msi"))
    #: (frozenset) Task options shared by all task
    COMMON_OPTS = frozenset(("dry_run", "verbose"))
    #: (dict) define all supported arguments and their default values.
    #: This attribute must be defined by derived classes.
    DEFAULT_OPTS: dict = None
    #: (set) mandatory task options. 'task' is implicitly mandatory.
    #: This is validated by the task runner before starting the workflow.
    MANDATORY_OPTS: set = None

    def __init__(self, task_inst: "TaskInstance"):
        assert self.DEFAULT_OPTS is not None

        #: (TaskInstance)
        self.task_inst: "TaskInstance" = task_inst
        #: (dict) The actual arguments, i.e. the default values merged with
        #: (dict) passed options
        self.opts: dict = self.DEFAULT_OPTS.copy()
        self.opts.update(task_inst.task_def)

        check_arg(self.opts.get("dry_run"), bool)
        check_arg(self.opts.get("verbose"), int)

        #: (bool) true if `--dry-run` was passed to the CLI
        self.dry_run: bool = self.opts.get("dry_run")
        #: (int, default=3) 0..5
        self.verbose: int = self.opts.get("verbose")

    def __repr__(self):
        return self.to_str({})

    def to_str(self, context: TaskContext):
        return "{}()".format(self.__class__.__name__)

    def cli_arg(self, key: str, default=None):
        """Return a value from command line args.

        Tasks mus handle tha case that `args` is not undefined when not running
        as CLI or the command is "info" instead of "running" for example.
        """
        return self.task_inst.task_runner.cli_arg(key, default)

    # def get_arg(self, key: str, default=NO_DEFAULT):
    #     """Return a value from command line args.

    #     Tasks mus handle tha case that `args` is not undefined when not running
    #     as CLI or the command is "info" instead of "running" for example.
    #     """
    #     return self.task_inst.task_runner.get_arg(key, default)

    def _exec(self, args, *, quiet: bool = None):
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
        output = res.stdout
        try:
            output = output.decode()
        except UnicodeDecodeError:
            output = output.decode("mbcs")

        output = output.strip()
        msg = "`{}` returned code {}".format(" ".join(args), ret_code)

        if ret_code != 0:
            if opts.get("ignore_errors"):
                write(msg, level="warning", prefix=True, output=output)
                return True, None
            write(msg, level="error", prefix=True, output=output)
        elif quiet is not True and not opts.get("silent"):
            write(msg, level="debug", prefix=True, output=output)
        return ret_code, output

    def _check_twine_availability(self) -> Union[str, None]:

        # --- 1. twine available?

        if not shutil.which("twine"):
            return "`twine` not available."

        has_pypirc = Path.home().joinpath(".pypirc").is_file()
        has_pypi_url = has_pypirc or bool(os.environ.get("TWINE_REPOSITORY_URL"))
        # we cannot check for password, since it may be part of .pypirc
        # or read from keyring
        has_pypi_user = has_pypirc or bool(os.environ.get("TWINE_USERNAME"))
        if not (has_pypi_url and has_pypi_user):
            return "`twine` needs `~/.pypirc` or TWINE_... environment variables."

        # ... `twine` is available and configured.

        # TODO: Trying to find out if credentials really work
        #       Problem: twine always returns
        #           InvalidDistribution: Cannot find file (or expand pattern):
        #           'yabs_access_test_1658159364.0588188'
        #       even if credentials are incorrect

        # ret_code, _out = self._exec(
        #     [
        #         "twine",
        #         "upload",
        #         "--non-interactive",
        #         "--verbose",
        #         # "--skip-existing",
        #         "--disable-progress-bar",
        #         f"yabs_access_test_{time.time()}",
        #     ]
        # )
        # print(_out)

        # raise NotImplementedError
        return None  # no errors

    @classmethod
    def _check_default_opts(
        cls, task_runner: "TaskRunner", task_def: dict, index: int
    ) -> List[str]:
        """Called by task_runner.run()."""

        mandatory = {"task"}
        if cls.MANDATORY_OPTS:
            mandatory = mandatory.union(cls.MANDATORY_OPTS)
        known = set(cls.DEFAULT_OPTS.keys()).union(mandatory).union(cls.COMMON_OPTS)

        errors = check_dict_keys(
            task_def,
            known=known,
            mandatory=mandatory,
            prefix=f"{cls.__name__}({task_def['task']!r}): ",
            key_prefix=f"tasks.[{index}].{task_def['task']}.",
        )
        return errors

    @abstractclassmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        """Check task definition for errors.

        This allows static pre-checks before the actual workflow starts.

        Returns:
            (str|list|bool) Error message(s)
        """
        return True

    # @classmethod
    # def handle_cli_command(cls, parser, args):
    #     """Default implementation, when run as stand-alone CLI command."""
    #     # Convert args namespace to option dict items:
    #     opts = vars(args)
    #     # Create task instance
    #     task = cls(opts)
    #     # The TaskRunner would maintain a `context` dict, when running a
    #     # sequence of workflow tasks. Here we need to set-up a simple one:
    #     context = TaskContext(args, None)
    #     res = task.run(context=context)
    #     return res

    @abstractclassmethod
    def register_cli_command(cls, subparsers, parents, run_parser):  # noqa: B902
        """Let tasks add a sub-command and/or arguments to the 'run' command."""

    @abstractmethod
    def run(self, context: TaskContext):
        """"""
