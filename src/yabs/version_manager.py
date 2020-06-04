# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
import re
import tempfile
from abc import ABC, abstractmethod
from configparser import ConfigParser

import toml
from semantic_version import Version

from .util import check_arg, log_debug, log_info, log_warning, resolve_path

INCREMENTS = frozenset(("major", "minor", "patch", "prerelease", "postrelease"))


def copy_version(v, prerelease=None):
    return Version(major=v.major, minor=v.minor, patch=v.patch, prerelease=prerelease)


class SafeFileWriter:
    """Open a file for writing, create a backup and prevent corruption on errors.

    Example:
        with FileWriter(fspec, "wt") as f:
            # on enter:
            #   - Remove fspec.tmp if any
            #   - self.f = open(fspec.tmp, mode)

            f.write(...)

            # on exit:
            #   - Remove fspec.bak if any
            #   - Move fspec -> fspec.bak if fspec exists
            #   - Move fspec.tmp -> fspec
            # on error:
            #   - Close and remove fspec.tmp
    """

    backup_ext = "bak"
    temp_ext = "tmp"

    def __init__(
        self,
        fspec,
        mode,
        keep_backup=True,
        use_peer_tmp=True,
        keep_temp_on_error=False,
    ):
        if "w" not in mode:
            raise RuntimeError("`mode` must be writable")
        self.fspec = fspec
        self.mode = mode
        self.keep_backup = keep_backup
        self.use_peer_tmp = use_peer_tmp
        self.keep_temp_on_error = keep_temp_on_error
        self.f = None
        self.temp_file = None

    def __enter__(self):
        if self.use_peer_tmp:
            self.temp_file = "{}.{}".format(self.fspec, self.temp_ext.lstrip("."))
            if os.path.isfile(self.temp_file):
                os.remove(self.temp_file)
            self.f = open(self.temp_file, self.mode)
        else:
            self.f = tempfile.NamedTemporaryFile(self.mode, delete=True)
            self.temp_file = self.f.name
        return self.f

    def __exit__(self, exc_type, exc_value, traceback):
        self.f.close()
        if exc_type:
            if not self.keep_temp_on_error and self.use_peer_tmp:
                os.remove(self.temp_file)
            return
        bak_file = "{}.{}".format(self.fspec, self.backup_ext.lstrip("."))
        if os.path.isfile(bak_file):
            os.remove(bak_file)
        os.rename(self.fspec, bak_file)
        os.rename(self.temp_file, self.fspec)
        if not self.keep_backup:
            os.remove(bak_file)


class VersionFileParser(ABC):
    """Base class for config file parsers."""

    def __init__(self, root_path, opts):
        self.root_path = root_path
        self.opts = opts
        self.fspec = self._find_config_file()
        self._org_version = None
        self.version = None

    def __str__(self):
        return "{}(v{})@{}".format(self.__class__.__name__, self.version, self.fspec)

    @abstractmethod
    def _find_config_file(self):
        """Return the config file path for this parser type."""

    @abstractmethod
    def parse(self, replace_version=None):
        """Read self.fspec and extract the version string."""

    @abstractmethod
    def write(self):
        """Patch the version into self.fspec and extract the version string."""

    def set_version(self, version, write=False):
        """Set a new vesion string.
        Args:
            version (str):
        """
        check_arg(version, Version)
        self.version = version
        if write:
            self.write()


class TextFileParser(VersionFileParser):
    """Read/write version numbers from plain text files.


    """

    # These `version.type`s are handled by default.
    # It is also possible to set `version.match`, `version.template`:
    pattern_map = {
        "__version__": {
            "match": r"""__version__\s*=\s*["'](\d+\.\d+\.?\d*[-+\d\w]*).*["]""",
            # "match": "__version__\s*=\s*[" '"](\d+\.\d+\.?\d*[-+\d\w]*).*[' '"]',
            # "match": "__version__\s*=\s*[" '"](\d+\.\d+\.\d+).*[' '"]',
            "template": '__version__ = "{version}"',
        },
    }

    def __init__(self, root_path, opts):
        type_defaults = self.pattern_map.get(opts["type"])
        opts.setdefault("match", type_defaults["match"])
        opts.setdefault("template", type_defaults["template"])
        super().__init__(root_path, opts)

    def _find_config_file(self):
        """Return the config file path for this parser type."""
        # default_fspec = parser.find_config_file(self.root_path)
        fspec = self.opts.get("file")
        fspec = resolve_path(self.root_path, fspec, must_exist=True)
        if not fspec:
            raise RuntimeError("Invalid `version.file`: {}".format(fspec))
        return fspec

    def parse(self, replace_version=None):
        """Read self.fspec and extract the version string."""
        version = None
        pattern = self.opts.get("match")
        pattern = re.compile(pattern)
        with open(self.fspec, "rt") as fp:
            for line in fp.readlines():
                # log_debug(line.rstrip())
                res = pattern.search(line)
                if res:
                    version = res.groups()[0]
                    # print(res)
                    # print(res.groups())

        if version is None:
            raise RuntimeError(
                "Could not match version pattern `{}` in {}".format(
                    pattern.pattern, self.fspec
                )
            )
        version = Version(version)
        self.version = version
        self._org_version = version

    def write(self):
        """Patch the version into self.fspec and extract the version string."""
        template = self.opts["template"].format(version=self.version)
        pattern = self.opts["match"]
        pattern = re.compile(pattern)

        with SafeFileWriter(self.fspec, "wt", keep_backup=False) as target:
            # target is a temporary file until __exit__, so we can open
            # the source file again here
            with open(self.fspec, "rt") as source:
                for line in source.readlines():
                    # log_debug(line.rstrip())
                    res = pattern.search(line)
                    if res:
                        # version = res.groups()[0]
                        target.write(template + "\n")
                        log_debug(
                            "Write line `{}` -> `{}`".format(
                                line.strip(), template.strip()
                            )
                        )
                    else:
                        target.write(line)
            # source is closed now. The exit handler will move the temp file
            # to the target (i.e. the original source)...
        return


class SetupCfgFileParser(VersionFileParser):
    """Read/write version numbers from setup.cfg files."""

    # def __init__(self, root_path, opts):
    #     super().__init__(root_path, opts)

    def _find_config_file(self):
        fspec = self.opts.get("file", "setup.cfg")
        fspec = resolve_path(self.root_path, fspec, must_exist=True)
        return fspec

    def parse(self, replace_version=None):
        """Read self.fspec and extract the version string."""
        cfg = ConfigParser()
        cfg.read(self.fspec)
        version = cfg.get("metadata", "version")
        if version.startswith(("attr:", "file:", "find:", "find_namespace:")):
            raise RuntimeError(
                (
                    "The version is only referenced here: '{}'. "
                    + "Use the 'file' type for the target location instead."
                ).format(version)
            )
        version = Version(version)
        self.version = version
        self._org_version = version

    def write(self):
        """Patch the version into self.fspec and extract the version string."""
        raise NotImplementedError


class PyprojectTomlParser(VersionFileParser):
    """Read/write version numbers from pyproject.toml files."""

    # def __init__(self, root_path, opts):
    #     super().__init__(root_path, opts)

    def _find_config_file(self, root):
        fspec = self.opts.get("file", "pyproject.toml")
        fspec = resolve_path(self.root_path, fspec, must_exist=True)
        return fspec

    def parse(self, replace_version=None):
        """Read self.fspec and extract the version string."""
        cfg = toml.load(self.fspec)
        version = cfg.get("project", {}).get("version")
        version = Version(version)
        self.version = version
        self._org_version = version

    def write(self):
        """Patch the version into self.fspec and extract the version string."""
        raise NotImplementedError


class VersionFileManager:
    """
    Maintain a list of version locations.
    The first version parser is the 'master', additional following parsers
    are considered 'secondaries' (which will be kept in sync with master).
    """

    parser_map = {
        # "pyfile": TextFileParser,
        "pyproject": PyprojectTomlParser,
        "setup_cfg": SetupCfgFileParser,
    }

    def __init__(self, task_runner):
        self.task_runner = task_runner
        self.parsers = []
        self.org_version = None
        self.master_version = None
        self._scan_versions()

    def _scan_versions(self):
        root_path = self.task_runner.fspec
        version_opts = self.task_runner.get("version")
        if isinstance(version_opts, dict):
            version_opts = [version_opts]

        # Create a version parser for every configured location definition
        # (first is 'main', all others 'secondary')
        for vo in version_opts:
            check_arg(vo, dict)
            cfg_type = vo.get("type")
            if cfg_type is None:
                raise RuntimeError("Missing `version.type`: {}".format(vo))

            if cfg_type in TextFileParser.pattern_map:
                parser_cls = TextFileParser
            else:
                parser_cls = self.parser_map.get(cfg_type)

            if parser_cls is None:
                known_types = set(TextFileParser.pattern_map) | set(self.parser_map)
                raise RuntimeError(
                    "Invalid `version.type`: {!r} (expected: {})".format(
                        cfg_type, ", ".join(known_types)
                    )
                )

            parser = parser_cls(root_path, vo)

            # #
            # default_fspec = parser.find_config_file(root_path)
            # fspec = vo.get("file", default_fspec)
            # if not fspec:
            #     raise RuntimeError("Invalid `version.file`: {}".format(fspec))

            # fspec = resolve_path(root_path, fspec, must_exist=True)
            parser.parse()
            version = parser.version

            if self.master_version is None:
                if not version:
                    raise RuntimeError("Invalid version or no version found.")
                log_info("Parsed project version: {}".format(version))
                self.master_version = version
                self.org_version = version
            else:
                log_info("Secondary project version: {}".format(version))
            self.parsers.append(parser)
        return

    @classmethod
    def _inc_prerelease(cls, v, prefix=""):
        """Increment a version's prerelase component."""

        pre_tuple = v.prerelease
        if len(pre_tuple) == 0:  # "1.2.3" -> "1.2.3-0"
            return copy_version(v, [prefix + "0"])
        if len(pre_tuple) > 1:
            log_warning(
                "Discarding multiple prerelase identifiers in {}.".format(pre_tuple)
            )
        pre = pre_tuple[0]
        # We already have a prerelease like "1.2.3-0", "1.2.3-alpha3", "1.2.3-rc1"
        # TODO: https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
        match = re.match(r"^([a-zA-Z]*)([0-9]+)(.*)", pre)
        cur_prefix, number, rest = match.groups()
        number = int(number)
        if cur_prefix != prefix:
            log_warning(
                "Changing prerelase prefix from {!r} to {!r}.".format(
                    cur_prefix, prefix
                )
            )
        if rest:
            log_warning("Discarding prerelase sufffix {!r}.".format(rest))
        pre = "{}{}".format(prefix, number + 1)
        v_new = copy_version(v, [pre])
        return v_new

    def set_version(self, semver, write):
        check_arg(semver, Version)
        check_arg(write, bool)
        self.master_version = semver
        for parser in self.parsers:
            log_debug("Set version {}...".format(parser))
            parser.set_version(semver, write)
        return

    def reset_version(self, write):
        log_warning(
            "Reset version {} => {}...".format(self.org_version, self.master_version)
        )
        if self.master_version != self.org_version:
            self.set_version(self.org_version, write)
        return

    def bump(self, inc, write=False, prerelease_prefix="a", calc_only=False):
        check_arg(inc, str, condition=inc in INCREMENTS)
        v = self.master_version
        if inc == "major":
            # 1.2.3 -> 2.0.0
            v_next = v.next_major()
        elif inc == "minor":
            # 1.2.3 -> 1.3.0
            v_next = v.next_minor()
        elif inc == "patch":
            # 1.2.3 -> 1.2.4
            v_next = v.next_patch()
            # print("vv", v, v_next)
        elif inc == "prerelease":
            # 1.2.3   -> ERROR
            # 1.2.3-0 -> 1.2.3-1
            if not v.prerelease:
                raise RuntimeError(
                    "'prerelease' would go backwards; consider 'postrelease'"
                )
            v_next = self._inc_prerelease(v, prerelease_prefix)
        elif inc == "postrelease":
            if v.prerelease:
                # 1.2.3-0 -> 1.2.3-1
                v_next = self._inc_prerelease(v, prerelease_prefix)
            else:
                # 1.2.3   -> 1.2.4-0
                v_next = v.next_patch()
                # print(v_next)
                v_next = self._inc_prerelease(v_next, prerelease_prefix)
                # print(v_next)
        else:
            raise NotImplementedError

        log_debug("bump({}): {} -> {}".format(inc, v, v_next))
        if calc_only:
            return v_next
        self.set_version(v_next, write)
        return v_next
