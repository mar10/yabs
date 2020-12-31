# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
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
    logger,
    remove_directory,
)


def get_folder_file_names(folder):
    """Return folder files names as set."""
    p = Path(folder)
    name_set = set([e.name for e in p.iterdir()])
    return name_set


class BuildTask(WorkflowTask):
    DEFAULT_OPTS = {
        "clean": True,
        "revert_bump_on_error": True,
        "targets": ["sdist", "bdist_wheel"],
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["clean"], bool)
        check_arg(opts["revert_bump_on_error"], bool)
        check_arg(opts["targets"], list)

        unknown = set(opts["targets"]).difference(self.KNOWN_TARGETS)
        if unknown:
            raise ConfigError(
                "Unkown `pypi_release.targets` value: {}".format(", ".join(unknown))
            )

    def to_str(self, context):
        opts = self.opts
        args = "{}".format(", ".join(opts["targets"]))
        return "{}(targets {})".format(self.__class__.__name__, args)

    @classmethod
    def register_cli_command(cls, subparsers, parents, run_parser):
        """"""

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

        # It's hard to guess the resulting name of the created artifacts,
        # so if don't want to erase the target '/dist' folder, we need to
        #   1. Create / empty a temp folder
        #   2. Build into that temp folder
        #   3. Move files from temp to /dist (overwrite if neccessary)
        #   4. Record the paths of the artifacts in `context.artifacts`
        #   5. Remove temp folder
        #
        #   Following tasks (e.g. PypiReleaseTask, GithubReleaseTask) will
        #   refer to `context.artifacts`.
        #   If the build fails, we rollback a previous bump, before we stop.

        org_dist_dir = Path("dist").absolute().resolve()
        if not org_dist_dir.is_dir():
            if self.dry_run:
                log_dry("Creating dist folder: {}".format(org_dist_dir))
            else:
                log_info("Creating dist folder: {}".format(org_dist_dir))
                org_dist_dir.mkdir()
            # raise RuntimeError("Folder not found: {}".format(org_dist_dir))

        temp_dist_dir = Path("dist.yabs").absolute().resolve()
        if temp_dist_dir.exists():
            remove_directory(temp_dist_dir, content_only=True, log=logger.info)
        else:
            temp_dist_dir.mkdir()

        for target in self.opts["targets"]:
            log_info("Building {} for {} {}...".format(target, real_name, real_version))
            prev_artifacts = get_folder_file_names(temp_dist_dir)
            ret_code, _out = self._exec(
                ["python", "setup.py", target, "--dist-dir", str(temp_dist_dir)]
                + extra_args
            )
            new_artifacts = list(
                get_folder_file_names(temp_dist_dir).difference(prev_artifacts)
            )
            ok = ok and (ret_code == 0)
            if len(new_artifacts) != 1:
                raise RuntimeError(
                    "Created {} artifacts (expected 1): {}".format(
                        len(new_artifacts), new_artifacts
                    )
                )
            artifact = new_artifacts[0]

            context.artifacts[target] = artifact

            if ret_code == 0:
                log_ok(
                    "Created '{}': {} {}: {}".format(
                        target, real_name, real_version, artifact
                    )
                )
            else:
                log_error(
                    "Failed to build '{}': {} {} {}".format(
                        target, real_name, real_version, ", ".join(new_artifacts)
                    )
                )

        # Validate result by calling `twine check FOLDER`
        twine_pattern = "{}/*".format(temp_dist_dir)
        ret_code, _out = self._exec(["twine", "check", twine_pattern])
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

        # Adjust artifact paths (temp -> dist):
        d = {}
        for target, path in context.artifacts.items():
            path_new = org_dist_dir.joinpath(Path(path).name)
            if not path_new.is_file() and not self.dry_run:
                raise RuntimeError("Artifact not found {}".format(path_new))
            d[target] = path_new
        context.artifacts = d

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
