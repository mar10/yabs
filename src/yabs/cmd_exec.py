# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import subprocess

from .cmd_common import WorkflowTask
from .util import check_arg, log_dry, log_response


class ExecTask(WorkflowTask):
    DEFAULT_OPTS = {
        "args": [],
        "dry_run_args": None,
        "always": False,
        "silent": False,
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
        check_arg(opts["timeout"], int, or_none=True)
        if opts["dry_run_args"] and opts["always"]:
            raise RuntimeError("`dry_run_args` and `always` are mutually exclusive")

    def to_str(self, context):
        opts = self.opts
        if self.dry_run and opts["dry_run_args"] is not None:
            args = opts["dry_run_args"]
        else:
            args = opts["args"]
        return "{}(`{}`)".format(self.__class__.__name__, " ".join(args))

    @classmethod
    def register_cli_command(cls, subparsers, parents):
        """"""
        sp = subparsers.add_parser(
            "exec", parents=parents, help="execute shell command",
        )
        sp.add_argument(
            "args", nargs="+", help="shell command and arguments",
        )
        sp.set_defaults(command=cls.handle_cli_command)

    def run(self, context):
        opts = self.opts

        args = opts["args"]
        if self.dry_run:
            if not opts["always"] and opts["dry_run_args"] is None:
                log_dry("Execute {}".format(" ".join(opts["args"])))
                return True
            if opts["dry_run_args"] is not None:
                args = opts["dry_run_args"]

        res = subprocess.run(
            args,
            timeout=opts["timeout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        )
        ret_code = res.returncode
        output = res.stdout.decode()
        msg = "{} returned code {}".format(self.to_str(context), ret_code)

        if ret_code != 0:
            if opts["ignore_errors"]:
                log_response(msg, output, "warning", False)
                return True
            log_response(msg, output, "error", False)
        elif not opts["silent"]:
            log_response(msg, output, "info", False)

        return ret_code == 0
