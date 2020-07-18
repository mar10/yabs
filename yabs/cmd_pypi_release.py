# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pathlib import Path

from .cmd_common import WorkflowTask
from .util import (
    ConfigError,
    check_arg,
    log_dry,
    log_error,
    log_info,
    log_ok,
    log_warning,
    logger,
    remove_directory,
)


def get_folder_file_names(folder):
    """Return folder files names as set."""
    p = Path(folder)
    name_set = set([e.name for e in p.iterdir()])
    return name_set


class PypiReleaseTask(WorkflowTask):
    KNOWN_TARGETS = ("sdist", "bdist_wheel", "bdist_msi")
    DEFAULT_OPTS = {
        "build": ["sdist", "bdist_wheel"],
        "clean": True,
        "ignore_errors": False,
        "revert_bump_on_error": True,
        "silent": False,
        "upload": False,
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["clean"], bool)
        check_arg(opts["build"], list)
        unknown = set(opts["build"]).difference(set(self.KNOWN_TARGETS))
        if unknown:
            raise ConfigError(
                "Unkown `pypi_release.build` value: {}".format(", ".join(unknown))
            )
        check_arg(opts["upload"], bool)

    def to_str(self, context):
        opts = self.opts
        args = "{}".format(", ".join(opts["build"]))
        if opts["upload"]:
            args += " & upload"
        return "{}(build {})".format(self.__class__.__name__, args)

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""
        # sp = subparsers.add_parser(
        #     "pypi-release",
        #     parents=parents,
        #     help="Make sdist, wheel, and upload on PyPI",
        # )
        # sp.add_argument(
        #     "--clean", action="store_true", help="erase dist folder before building",
        # )
        # sp.add_argument(
        #     "--upload",
        #     action="store_true",
        #     help="upload built artefacts to PyPI using twine",
        # )
        # sp.add_argument(
        #     "--build",
        #     choices=cls.KNOWN_TARGETS,
        #     nargs="*",
        #     help="call setup.py to build artefacts (option may be repeated, default: sdist, bdist_wheel)",
        # )
        # sp.set_defaults(command=cls.handle_cli_command)

    def _run(self, context):
        opts = self.opts
        ok = True

        extra_args = []
        # NOTE: `--dry-run` flag does not work well with setup.py?
        #    Seems to produce errors like
        #    "error: [Errno 2] No such file or directory: 'test-release-tool-0.0.1/PKG-INFO'"
        # if self.dry_run:
        #     extra_args.append("--dry-run")

        if self.verbose >= 4:
            extra_args.append("--verbose")
        elif self.verbose <= 2:
            extra_args.append("--quiet")

        # Check if setup.py really uses the expected name & version
        ret_code, real_name = self._exec(["python", "setup.py", "--name"] + extra_args)
        ret_code, real_version = self._exec(
            ["python", "setup.py", "--version"] + extra_args
        )

        if real_version != str(context.version):
            if not self.dry_run:
                raise RuntimeError(
                    "`setup.py --version` returned {} (expected {})".format(
                        real_version, context.version
                    )
                )

        # It's hard to guess the resulting name of the created artefacts,
        # so if don't want to erase the target '/dist' folder, we need to
        #   1. create / empty a temp folder
        #   2. build into that temp folder
        #   3. twine upload that folder
        #   4. move files from temp to /dist (overwrite if neccessary
        #   5. remove temp folder
        # org_dist_dir = os.path.abspath("dist")
        org_dist_dir = Path("dist").absolute().resolve()
        if not org_dist_dir.is_dir():
            raise RuntimeError("Folder not found: {}".format(org_dist_dir))

        temp_dist_dir = Path("dist.yabs").absolute().resolve()
        if temp_dist_dir.exists():
            remove_directory(temp_dist_dir, content_only=True, log=logger.info)
        else:
            temp_dist_dir.mkdir()

        extra_args
        # dist_files = []
        # dist_prefix = "{}-{}".format(real_name, real_version)

        for target in self.opts["build"]:
            log_info("Building {} for {} {}...".format(target, real_name, real_version))
            prev_artefacts = get_folder_file_names(temp_dist_dir)
            ret_code, _out = self._exec(
                ["python", "setup.py", target, "--dist-dir", str(temp_dist_dir)]
                + extra_args
            )
            new_artefacts = list(
                get_folder_file_names(temp_dist_dir).difference(prev_artefacts)
            )
            # print("1", prev_artefacts)
            # print("2", new_artefacts)
            ok = ok and (ret_code == 0)
            if len(new_artefacts) != 1:
                raise RuntimeError(
                    "Created {} artefacts (expected 1): {}".format(
                        len(new_artefacts), new_artefacts
                    )
                )
            artefact = new_artefacts[0]

            context.artefacts[target] = artefact

            if ret_code == 0:
                log_ok(
                    "Created '{}': {} {}: {}".format(
                        target, real_name, real_version, artefact
                    )
                )
            else:
                log_error(
                    "Failed to build '{}': {} {} {}".format(
                        target, real_name, real_version, ", ".join(new_artefacts)
                    )
                )

        twine_pattern = "{}/*".format(temp_dist_dir)
        ret_code, _out = self._exec(["twine", "check", twine_pattern])
        ok = ok and (ret_code == 0)

        if opts["upload"]:
            if context._args.no_release:
                log_warning(
                    "`--no-release` was passed: skipping `twine upload` of 'pypi_release' task."
                )
            elif self.dry_run:
                log_dry("twine upload {}".format(twine_pattern))
            else:
                # TODO: uses .pypirc
                ret_code, _out = self._exec(
                    [
                        "twine",
                        "upload",
                        "--non-interactive",
                        "--verbose",
                        # "--skip-existing",
                        "--disable-progress-bar",
                        twine_pattern,
                    ]
                )
                ok = ok and (ret_code == 0)

        for src in temp_dist_dir.iterdir():
            if self.dry_run:
                log_dry("Move {} => {}".format(src, org_dist_dir.joinpath(src.name)))
            else:
                log_info("Move {} => {}".format(src, org_dist_dir.joinpath(src.name)))
                src.replace(org_dist_dir.joinpath(src.name))
        # Remove the temp folder (even in dry-run), since we don't want to
        # commit it:
        remove_directory(temp_dist_dir, log=logger.info)
        # Adjust artefact paths:
        d = {}
        for target, path in context.artefacts.items():
            path_new = org_dist_dir.joinpath(Path(path).name)
            if not path_new.is_file() and not self.dry_run:
                raise RuntimeError("Artefact not found {}".format(path_new))
            d[target] = path_new
        context.artefacts = d
        # print("np", context.artefacts)

        if opts["clean"]:
            ret_code, _out = self._exec(
                ["python", "setup.py", "clean", "--all"] + extra_args
            )
            ok = ok and (ret_code == 0)

        return ok

    @classmethod
    def check_task_def(cls, task_def, parser, args, yaml):
        return True

    def run(self, context):
        try:
            res = self._run(context)
            if res:
                return res
        except Exception as e:
            log_error("{}".format(e))

        if self.opts["revert_bump_on_error"] and not self.dry_run:
            # log_warning("Reverting bump {} => {} ...".format(vm.master_version, context.version))
            vm = context.version_manager
            vm.reset_version(write=not self.dry_run)
            context.version = vm.master_version

        return False
