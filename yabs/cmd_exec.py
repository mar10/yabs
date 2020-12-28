# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import subprocess
import time

from .cmd_common import WorkflowTask
from .util import (
    check_arg,
    format_elap,
    log_debug,
    log_dry,
    log_info,
    log_response,
    run_process_streamed,
)


class ExecTask(WorkflowTask):
    DEFAULT_OPTS = {
        "args": [],
        "dry_run_args": None,
        "always": False,
        "silent": False,
        "log_start": True,
        "stream": None,
        "ignore_errors": False,
        "timeout": None,
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["args"], (list, tuple))
        check_arg(opts["dry_run_args"], (list, tuple), or_none=True)
        check_arg(opts["silent"], bool)
        check_arg(opts["always"], bool)
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

    def to_str(self, context):
        opts = self.opts
        if self.dry_run and opts["dry_run_args"] is not None:
            args = opts["dry_run_args"]
        else:
            args = opts["args"]
        return "{}(`{}`)".format(self.__class__.__name__, " ".join(args))

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

    @classmethod
    def check_task_def(cls, task_def, parser, args, yaml):
        return True

    def run(self, context):
        opts = self.opts
        name = self.to_str(context)

        args = opts["args"]
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
        if stream:
            with subprocess.Popen(args, **popen_opts) as proc:
                # interval = 1.0 if stream is True else float(stream)
                ret_code, output = run_process_streamed(proc, name, timeout=timeout)
                output = ""  # already printed
        else:
            proc = subprocess.run(args, timeout=timeout, **popen_opts)
            ret_code = proc.returncode
            output = proc.stdout.decode()

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
