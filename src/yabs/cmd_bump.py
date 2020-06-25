# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from .cmd_common import WorkflowTask
from .util import check_arg, ConfigError, log_error, log_warning
from .version_manager import INCREMENTS


class BumpTask(WorkflowTask):
    DEFAULT_OPTS = {
        "inc": None,
        "check": True,
        "prerelease_prefix": "a",
    }

    def __init__(self, opts):
        super().__init__(opts)
        opts = self.opts
        check_arg(
            opts["inc"], str, or_none=True, condition=opts.get("inc") in INCREMENTS
        )
        check_arg(opts["check"], bool)
        check_arg(opts["prerelease_prefix"], str)

    def to_str(self, context):
        if context:
            inc = self.opts["inc"] or context.inc
            version = context.version_manager.master_version
            return "{}({!r}) => v{}".format(self.__class__.__name__, inc, version)
        return "{}({!r})".format(self.__class__.__name__, self.opts["inc"])

    @classmethod
    def register_cli_command(cls, subparsers, parents):
        """"""
        sp = subparsers.add_parser(
            "bump", parents=parents, help="increment current project version",
        )
        sp.add_argument(
            "inc",
            choices=["major", "minor", "patch", "postrelease"],
            # default="patch",
            help="bump semantic version by this increment",
        )
        sp.add_argument(
            "--check",
            action="store_true",
            help="test afterwards if `setup.py --version` matches",
        )
        sp.set_defaults(command=cls.handle_cli_command)

    def run(self, context):
        opts = self.opts
        dry_run = context.dry_run
        if context._args.no_bump:
            log_warning("`--no-bump` was passed: forcing dry-run mode for 'bump' task.")
            dry_run = True

        inc = opts.get("inc")
        if not inc:
            if context.inc:
                inc = context.inc
            else:
                raise ConfigError(
                    "Missing bump increment: either define `inc` option or pass `inc` argument."
                )
        if inc not in INCREMENTS:
            raise ConfigError(
                "Invalid `inc` option '{}' (expected {}).".format(
                    inc, ", ".join(INCREMENTS)
                )
            )

        vm = context.version_manager
        vm.bump(inc, prerelease_prefix=opts["prerelease_prefix"], write=not dry_run)
        context.version = vm.master_version

        if opts["check"] and not dry_run:
            _ret_code, real_version = self._exec(["python", "setup.py", "--version"])
            if real_version != str(vm.master_version):
                log_error(
                    "`setup.py --version` returned {} (expected {}).".format(
                        real_version, vm.master_version
                    )
                )
                return False

        return True
