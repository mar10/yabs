# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ..util import (
    FolderContentMonitor,
    check_arg,
    format_elap,
    log_debug,
    log_dry,
    log_info,
    log_response,
    log_warning,
    run_process_streamed,
)
from .common import TaskContext, WorkflowTask

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from yabs.task_runner import TaskInstance


class ExecTask(WorkflowTask):
    DEFAULT_OPTS = {
        "args": [],
        "add_artifacts": None,
        "always": False,
        "dry_run_args": None,
        "ignore_errors": False,
        "log_start": True,
        "silent": False,
        "stream": None,
        "timeout": None,
    }
    MANDATORY_OPTS = {"args"}

    def __init__(self, task_inst: "TaskInstance"):
        super().__init__(task_inst)

        opts = self.opts
        check_arg(opts["args"], (list, tuple))
        check_arg(opts["dry_run_args"], (list, tuple), or_none=True)
        check_arg(opts["silent"], bool)
        check_arg(opts["always"], bool)
        check_arg(opts["add_artifacts"], dict, or_none=True)
        check_arg(opts["ignore_errors"], bool)
        check_arg(opts["log_start"], bool)
        check_arg(opts["stream"], bool, or_none=True)
        check_arg(opts["timeout"], (int, float), or_none=True)
        if opts["dry_run_args"] and opts["always"]:
            raise RuntimeError("`dry_run_args` and `always` are mutually exclusive")
        if opts["silent"] and opts["stream"]:
            raise RuntimeError("`silent` and `stream` are mutually exclusive")
        if opts["stream"] is None and opts["verbose"] > 3:
            log_debug("Enabling streaming output in verbose mode.")
            opts["stream"] = True
        return

    def to_str(self, context: TaskContext):
        opts = self.opts
        if self.dry_run and opts["dry_run_args"] is not None:
            args = opts["dry_run_args"]
        else:
            args = opts["args"]

        path = Path(args[0])
        if path.is_file():
            args = args.copy()
            args[0] = path.name
        return "{}(`{}`)".format(self.__class__.__name__, " ".join(args))

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    @classmethod
    def check_task_def(cls, task_inst: "TaskInstance"):
        task_def = task_inst.task_def
        arts = task_def.get("add_artifacts")
        errors = []
        if arts:
            err = (
                "execute.add_artifacts.matches must be a dict: "
                "{ 'folder: FOLDER, 'matches': {TAG_1: PATTERN_1, ...} }` "
                f" (got : {arts})"
            )
            if type(arts) is not dict or type(arts.get("folder")) is not str:
                raise ValueError(err)

            matches = arts.get("matches")
            if type(matches) is not dict:
                raise ValueError(err)
            for tag, pattern in matches.items():
                try:
                    re.compile(pattern)
                except re.error:
                    errors.append(
                        f"Invalid regex: add_artifacts.matches.pattern: {tag}: {pattern!r}"
                    )
        return errors or True

    def run(self, context: TaskContext):
        opts = self.opts
        name = self.to_str(context)

        args = opts["args"]

        # Fix python calls to use the executable from the virtual environment
        if args[0].lower() == "python":
            args[0] = sys.executable

        if self.dry_run:
            if not opts["always"] and opts["dry_run_args"] is None:
                log_dry("Execute {}".format(" ".join(opts["args"])))
                return True
            if opts["dry_run_args"] is not None:
                args = opts["dry_run_args"]
        if opts["log_start"]:
            msg = "Running {}...".format(name)
            log_info(msg)

        timeout = opts["timeout"]
        popen_opts = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "shell": False,
        }
        stream = opts["stream"]
        start = time.time()

        artifacts_def = opts["add_artifacts"]
        with FolderContentMonitor(artifacts_def) as fcm:
            if stream:
                with subprocess.Popen(args, **popen_opts) as proc:
                    # interval = 1.0 if stream is True else float(stream)
                    ret_code, output = run_process_streamed(proc, name, timeout=timeout)
                    output = ""  # already printed
            else:
                proc = subprocess.run(args, timeout=timeout, **popen_opts)
                ret_code = proc.returncode
                output = proc.stdout.decode()

        if fcm.changed_or_added_files:
            # log_info(f"Created artifacts: {fcm.changed_or_added_files}")
            log_info(f"Created artifacts: {fcm.changed_or_added_by_tag}")
            context.artifacts.update(fcm.changed_or_added_by_tag)
        elif artifacts_def:
            log_warning(f"No artifacts created for `add_artifacts: {artifacts_def}`")
        log_debug(f"Available artifacts: {context.artifacts}")

        elap = time.time() - start
        msg = "{} returned code {} ({})".format(name, ret_code, format_elap(elap))

        if ret_code != 0:
            if opts["ignore_errors"]:
                log_response(msg, output, "warning", False)
                return True
            log_response(msg, output, "error", False)
        elif not opts["silent"]:
            log_response(msg, output, "info", False)

        return ret_code == 0
