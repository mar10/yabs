# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import logging
import math
import os
import re
import sys
import time
import types
import warnings
from datetime import datetime
from io import StringIO
from pathlib import Path
from shutil import rmtree
from threading import Event, RLock, Thread
from typing import List, Tuple, Union

from snazzy import Snazzy, emoji, gray, green, red, yellow

logger = logging.getLogger("yabs")

CONFIG_NAME = "yabs.yaml"


class YabsError(RuntimeError):
    """Base class for all exception that we deliberatly throw."""


class ExitingYabsError(SystemExit, YabsError):
    """
    YabsError the will cause sys.exit().
    Raised for errors that don't need a stack trace.
    """


class CheckError(ExitingYabsError):
    """--check condition failed."""


class ConfigError(ExitingYabsError):
    """Invalid yabs.yaml or command line (terminates without stacktrace)."""


class NO_DEFAULT:
    """Used as default parameter to distinguish from `None`."""


def get_folder_file_names(folder):
    """Return folder files names as set."""
    p = Path(folder)
    name_set = set([e.name for e in p.iterdir()])
    return name_set


class FolderContentMonitor:
    def __init__(
        self, artifacts_def: Union[dict, None], *, create_folder: bool = False
    ) -> None:
        self.artifacts_def = artifacts_def
        self.path = None
        self.create_folder = create_folder
        self.prev_files = None
        self.cur_files = None
        self.added_files = None
        self.changed_or_added_files = None
        self.changed_or_added_by_tag = None
        if artifacts_def:
            self.path = Path(artifacts_def["folder"]).absolute()

    def __enter__(self):
        path = self.path
        if not path:
            return self

        if not path.is_dir():
            if not self.create_folder:
                raise ValueError(f"Folder not found: {path}")
            # elif self.dry_run:
            #     log_dry(f"Creating dist folder: {path}")
            else:
                log_info(f"Creating dist folder: {path}")
                path.mkdir()

        self.prev_stats = {}
        for e in path.iterdir():
            self.prev_stats[e.name] = e.stat()
        self.prev_files = set(self.prev_stats.keys())

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.path:
            return

        self.added_files = set()
        self.changed_or_added_files = set()
        self.changed_or_added_by_tag = {}
        for e in self.path.iterdir():
            cur_stat = e.stat()
            prev_stat = self.prev_stats.get(e.name)
            if prev_stat is None:
                self.added_files.add(e.name)
                self.changed_or_added_files.add(e.name)
            elif cur_stat.st_mtime != prev_stat.st_mtime:
                self.changed_or_added_files.add(e.name)

        for fspec in self.changed_or_added_files:
            for tag, pattern in self.artifacts_def["matches"].items():
                # print("MATCH", tag, pattern, fspec)
                if re.match(pattern, fspec):
                    full_path = (self.path / fspec).absolute()
                    self.changed_or_added_by_tag[tag] = full_path
        return


def init_logging(verbose=3, path=None):
    """CLI calls this."""
    if verbose < 1:
        level = logging.CRITICAL
    elif verbose < 2:
        level = logging.ERROR
    elif verbose < 3:
        level = logging.WARNING
    elif verbose < 4:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(message)s",
        # format="%(asctime)-8s.%(msecs)-3d <%(thread)05d> %(levelname)-7s %(message)s",
        # format="%(asctime)s.%(msecs)03d <%(process)d.%(thread)d> %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    # If basicConfig() was already called before, the above call was a no-op.
    # Make sure, we adjust the level still:
    logging.root.setLevel(level)

    if path:
        if os.path.isdir(path):
            fname = "release-tool_{}.log".format(timetag())
            path = os.path.join(path, fname)
        logger.info("Writing log to '{}'".format(path))
        if os.path.isfile(path):
            logger.warning("Removing log file '{}'".format(path))
            os.remove(path)
        hdlr = logging.FileHandler(path)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)-3d - %(levelname)s: %(message)s", "%H:%M:%S"
        )
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        # logger.setLevel(logging.DEBUG)
        logger.info("Start log ({})".format(datetime.now()))
        logger.info("Running {}".format(" ".join(sys.argv)))

        # redirect `logger` to our special log file as well:
        logger.addHandler(hdlr)

    # Silence requests `InsecureRequestWarning` messages
    if verbose <= 3:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    else:
        warnings.filterwarnings("once", message="Unverified HTTPS request")

    return logger


def check_cli_verbose(default=3):
    """Check for presence of `--verbose`/`--quiet` or `-v`/`-q` without using argparse."""
    args = sys.argv[1:]
    verbose = default + args.count("--verbose") - args.count("--quiet")

    for arg in args:
        if arg.startswith("-") and not arg.startswith("--"):
            verbose += arg[1:].count("v")
            verbose -= arg[1:].count("q")
    return verbose


_prefix_map = None
_prefix_map_valid = False


def write(msg: str, *, level="info", prefix=False, output=None, output_level=None):
    """"""
    # We want to cache the color formatted strings, however the
    # `snazzy` formatter may not be initialized yet.
    # So we may have to defer this caching here:
    global _prefix_map, _prefix_map_valid

    if not _prefix_map_valid:
        _prefix_map = {
            False: {},
            True: {
                "info": green("OK") + ": ",
                "warning": yellow("WARNING") + ": ",
                "error": red("ERROR") + ": ",
            },
            # Use emoji if terminal supports it, colored ASCII otherwise
            "check": {
                "info": "    {} ".format(emoji("✅", green("*"))),
                "warning": "    {} ".format(emoji("❗", yellow("!"))),
                "error": "    {} ".format(emoji("❌", red("X"))),
            },
        }
        if Snazzy._initialized:
            _prefix_map_valid = True

    level_name = level
    level = logging._nameToLevel[level_name.upper()]
    assert prefix in _prefix_map.keys(), prefix
    if output_level is None:
        output_level = level
    else:
        output_level = logging._nameToLevel[output_level.upper()]

    prefix = _prefix_map[prefix].get(level_name, "")
    logger.log(level, prefix + msg)

    if output:
        prefix_len = len(Snazzy.cleanup(prefix))
        prefix = (" " * prefix_len) + " > "
        lines = output.split("\n")
        # strip trailing empty lines
        while len(lines) > 1 and not lines[-1]:
            lines.pop()
        output = prefix + ("\n" + prefix).join(lines)

        if output_level == "debug":
            output = gray(output)
        logger.log(output_level, output)

    return


def log_debug(msg):
    return write(msg, level="debug", prefix=False)


def log_info(msg):
    return write(msg, level="info", prefix=False)


def log_dry(msg):
    return write("DRY-RUN " + msg, level="info", prefix=False)


def log_response(info, output, level, dry_run):
    return write(info, level=level, prefix=True, output=output)


def log_ok(msg):
    return write(msg, level="info", prefix=True)


def log_warning(msg):
    return write(msg, level="warning", prefix=True)


def log_error(msg):
    return write(msg, level="error", prefix=True)


def set_console_ctrl_handler(
    ctrl_handler, do_ctrl_c=True, do_ctrl_break=False, do_ctrl_close=False
):
    """

    The do_ctrl_* functions could simply be sys.exit(1), which will ensure that
    atexit handlers get called.
    See https://bugs.python.org/issue35935

    Raises:
        ctypes.WinError
    Returns:
        False if not on Windows or could not register the handler.
    """
    if os.name != "nt":
        return False

    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        logger.info("Loaded kernel32 DLL on Windows.")
    except Exception as e:
        logger.warning("Could not load kernel32 DLL on Windows: {}".format(e))
        return False

    CTRL_C_EVENT = 0
    CTRL_BREAK_EVENT = 1
    CTRL_CLOSE_EVENT = 2

    HANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    kernel32.SetConsoleCtrlHandler.argtypes = (HANDLER_ROUTINE, wintypes.BOOL)

    @HANDLER_ROUTINE
    def handler(ctrl):
        if ctrl == CTRL_C_EVENT and do_ctrl_c:
            handled = ctrl_handler(ctrl)
        elif ctrl == CTRL_BREAK_EVENT and do_ctrl_break:
            handled = ctrl_handler(ctrl)
        elif ctrl == CTRL_CLOSE_EVENT and do_ctrl_close:
            handled = ctrl_handler(ctrl)
        else:
            handled = False
        # If not handled, call the next handler.
        return handled

    if not kernel32.SetConsoleCtrlHandler(handler, True):
        raise ctypes.WinError(ctypes.get_last_error())
    return True


def assert_always(condition, msg=None):
    """`assert` even in production code."""
    try:
        if not condition:
            raise AssertionError(msg) if msg is not None else AssertionError
    except AssertionError as e:
        if sys.version_info < (3, 7):
            raise
        # Strip last frames, so the exception's stacktrace points to the call
        # Credits: https://stackoverflow.com/a/58821552/19166
        _exc_type, _exc_value, traceback = sys.exc_info()
        back_frame = traceback.tb_frame.f_back

        back_tb = types.TracebackType(
            tb_next=None,
            tb_frame=back_frame,
            tb_lasti=back_frame.f_lasti,
            tb_lineno=back_frame.f_lineno,
        )
        raise e.with_traceback(back_tb)


def _check_arg(argument, types, condition, accept_none):
    if __debug__:
        err_msg = "`allowed_types` must be a type or class (or a tuple thereof): got instance of {}"
        if isinstance(types, tuple):
            for t in types:
                assert isinstance(t, type), err_msg.format(type(t))
        else:
            assert isinstance(types, type), err_msg.format(type(types))

    if accept_none:
        if argument is None:
            return
        extra_msg = "`None` or "
    else:
        extra_msg = ""

    if not isinstance(argument, types):
        raise TypeError(
            "Expected {}{}, but got {}".format(extra_msg, types, type(argument))
        )
    if condition is not NO_DEFAULT and not bool(condition):
        raise ValueError(
            "Invalid argument value: {} {}".format(type(argument), argument)
        )


def check_arg(argument, allowed_types, condition=NO_DEFAULT, *, or_none=False):
    """Check if `argument` has the expected type and value.

    **Note:** the exception's traceback is manipulated, so that the back frame
    points to the ``check_arg()`` line, instead of the actual ``raise``.

    Args:
        argument (any): value of the argument to check
        allowed_types (type or tuple of types)
        condition (bool, optional): additional condition that must be true
        or_none (bool, optional): defaults to false
    Returns:
        None
    Raises:
        TypeError: if `argument` is of an unexpected type
        ValueError: if `argument` does not fulfill the optional condition
        AssertionError:
            if `check_arg` was called with a wrong syntax, i.e. `allowed_types`
            does not contain types, e.g. if `1` was passed instead of `int`.

    Examples::

        def foo(name, amount, options=None):
            check_arg(name, str)
            check_arg(amount, (int, float), amount > 0)
            check_arg(options, dict, or_none=True)
    """
    try:
        _check_arg(argument, allowed_types, condition, accept_none=or_none)
    except (TypeError, ValueError) as e:
        if sys.version_info < (3, 7):
            raise
        # Strip last frames, so the exception's stacktrace points to the call
        _exc_type, _exc_value, traceback = sys.exc_info()
        back_frame = traceback.tb_frame.f_back

        back_tb = types.TracebackType(
            tb_next=None,
            tb_frame=back_frame,
            tb_lasti=back_frame.f_lasti,
            tb_lineno=back_frame.f_lineno,
        )
        raise e.with_traceback(back_tb)


def to_list(obj, or_none=False):
    """Convert a single object to a list."""
    if obj is None:
        return None if or_none else []
    elif isinstance(obj, (list, tuple)):
        return obj
    elif isinstance(obj, set):
        return list(obj)
    return [obj]  # may ba a str


def to_set(obj, or_none=False):
    """Convert a single object to a set."""
    if obj is None and or_none:
        return None
    if isinstance(obj, set):
        return obj
    return set(to_list(obj))


def get_dict_attr(d, key_path, default=NO_DEFAULT):
    """Return the value of a nested dict using dot-notation path.

    Args:
        d (dict):
        key_path (str):
    Raises:
        KeyError:
        ValueError:
        IndexError:

    Examples::

        ...

    Todo:
        * k[1] instead of k.[1]
        * default arg
    """
    if default is not NO_DEFAULT:
        try:
            return get_dict_attr(d, key_path)
        except (AttributeError, KeyError, ValueError, IndexError):
            return default

    check_arg(d, dict)

    seg_list = key_path.split(".")
    value = d[seg_list[0]]
    for seg in seg_list[1:]:
        if isinstance(value, dict):
            value = value[seg]
        elif isinstance(value, (list, tuple)):
            if not seg.startswith("[") or not seg.endswith("]"):
                raise ValueError("Use `[INT]` syntax to address list items")
            seg = seg[1:-1]
            value = value[int(seg)]
        else:
            # raise ValueError("Segment '{}' cannot be nested".format(seg))
            try:
                value = getattr(value, seg)
            except AttributeError:
                raise  # ValueError("Segment '{}' cannot be nested".format(seg))

    return value


def check_dict_keys(
    d: dict, *, known: set, mandatory: set, prefix: str, key_prefix: str = ""
) -> List[str]:
    """Validate a dict fo missing or unknown keys."""
    used = set(d.keys())
    known = known.union(mandatory)
    missing = mandatory.difference(used)

    errors = []

    if missing:
        s1 = ", ".join(sorted(f"`{key_prefix}{s}`" for s in missing))
        errors.append(f"{prefix}Missing mandatory option(s): {s1}")

    invalid = used.difference(known)
    if invalid:
        unused = known.difference(used)
        s1 = ", ".join(sorted(f"`{key_prefix}{s}`" for s in invalid))
        s2 = "'" + "', '".join(sorted(unused)) + "'"
        errors.append(f"{prefix}Unsupported option(s): {s1} (did you mean {s2} ?)")

    return errors


def timetag(seconds=True, *, ms=False):
    """Return a time stamp string that can be used as (part of a) filename (also sorts well)."""
    now = datetime.now()
    if ms or seconds:
        s = now.strftime("%Y%m%d_%H%M%S")
        if ms:
            s = "{}_{}".format(s, now.microsecond)
    else:
        s = now.strftime("%Y%m%d_%H%M")
    return s


def resolve_path(root, path, must_exist=True, check_root=False):
    """Return an absolute path, assuming relative to the root file or folder."""
    if not os.path.isabs(path):
        if os.path.isfile(root):
            root = os.path.dirname(root)
        path = os.path.join(root, path)
    path = os.path.abspath(path)
    if check_root and not path.startswith(root):
        raise ValueError("Path must be in or below {}: {}".format(root, path))
    if must_exist and not os.path.isfile(path):
        raise ValueError("File not found: {}".format(path))
    return path


def search_file_upward(
    root: Union[str, Path], filename: str, *, max_level=0, or_none=False
) -> Path:
    """."""
    root = Path(root).expanduser().absolute()
    if root.is_file():
        return root
    assert root.is_dir(), root

    target = f"{root}/{filename}"
    cur_level = 0
    parents = [root] + list(root.parents)
    for parent in parents:
        fspec = parent / filename
        # print(f"Searching for {fspec}...")
        if fspec.is_file():
            return fspec
        cur_level += 1
        if max_level and cur_level >= max_level:
            break

    if not or_none:
        raise FileNotFoundError(f"{target}")
    return None


def remove_directory(path, content_only=False, log=None):
    check_arg(path, (str, Path))
    check_arg(content_only, bool)

    path = Path(path).absolute().resolve()
    if not path.is_dir():
        raise ValueError("Not a directory: {}".format(path))

    if content_only:
        for p in path.iterdir():
            if p.is_file():
                if log:
                    log("Removing file {}".format(p))
                p.unlink()
            elif p.is_dir():
                if log:
                    log("Removing directory {}".format(p))
                rmtree(p)
    else:
        if log:
            log("Removing directory {}".format(path))
        rmtree(path)
    return


def shorten_string(long_string, max_chars, min_tail_chars=0, place_holder="[...]"):
    """Return string, shortened to max_chars characters.

    long_string = "This is a long string, that will be truncated."
    trunacated_string = truncate_string(long_string, max_chars=26, min_tail_chars=11, place_holder="[...]")
    print trunacated_string
    >> This is a [...] truncated.

    @param long_string: string to be truncated
    @param max_chars: max chars of returned string
    @param min_tail_chars: minimum of tailing chars
    @param place_holder: place holder for striped content
    @return: truncated string
    """

    assert max_chars > (min_tail_chars + len(place_holder))

    # Other types aren't supported.
    if not isinstance(long_string, str):
        return long_string

    # If string is shorter then max_chars, it can be returned, as is.
    elif len(long_string) <= max_chars:
        return long_string

    # Making sure we don't exceed max_chars in total.
    prefix_length = max_chars - min_tail_chars - len(place_holder)

    if min_tail_chars:
        long_string = (
            long_string[:prefix_length] + place_holder + long_string[-min_tail_chars:]
        )
    else:
        long_string = long_string[:prefix_length] + place_holder

    assert len(long_string) == max_chars

    return long_string


def plural_s(value) -> str:
    """Return 's' if `value` is not singular.

    Example:
        from util import plural_s as ps

        v = [1, 2]
        print(f"Found value{ps(v)}: {v}")
    """
    if type(value) in (float, int):
        n = value
    elif isinstance(value, (dict, list, set, tuple)):
        n = len(value)
    else:  # type(value) is str:
        # May be None, str (assume 'one word', not: 'many characters') or other
        n = 1
    return "" if n == 1 else "s"


def datetime_to_iso(dt=None, microseconds=False):
    """Return current UTC datetime as ISO formatted string."""
    if dt is None:
        dt = datetime.now()
    if not microseconds:
        dt.replace(microsecond=0)
    return dt.isoformat(sep=" ")


# def iso_to_datetime(iso):
#     """Convert as ISO formatted datetime string to datetime."""
#     # dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%fZ")
#     dt = isoparse(iso)
#     return dt


# def iso_to_stamp(iso):
#     """Convert as ISO formatted datetime string to datetime."""
#     return iso_to_datetime(iso).timestamp()


def format_elap(
    seconds, *, count=None, unit="items", high_prec=False, short_suffix=False
):
    """Return elapsed time as H:M:S.h string with reasonable precision."""
    days, seconds = divmod(seconds, 86400) if seconds else (0, 0)

    if seconds >= 3600:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        suff = "h" if short_suffix else " hrs"
        if high_prec:
            res = f"{int(h):d}:{int(m):02d}:{s:04.1f}{suff}"
        else:
            res = f"{int(h):d}:{int(m):02d}:{int(s):02d}{suff}"
    elif seconds >= 60:
        m, s = divmod(seconds, 60)
        suff = "m" if short_suffix else " min"
        if high_prec:
            res = f"{int(m):d}:{s:05.2f}{suff}"
        else:
            res = f"{int(m):d}:{int(s):02d}{suff}"
    else:
        suff = "s" if short_suffix else " sec"
        if high_prec:
            res = f"{seconds:.3f}{suff}"
        elif seconds > 5:
            res = f"{seconds:.1f}{suff}"
        else:
            res = f"{seconds:.2f}{suff}"

    if days == 1:
        suff = "d" if short_suffix else " day"
        res = f"{int(days)}{suff} {res}"
    elif days:
        suff = "d" if short_suffix else " days"
        res = f"{int(days)}{suff} {res}"

    if count and (seconds > 0):
        suff = "s" if short_suffix else "sec"
        res += ", {:,.1f} {}/{}".format(float(count) / seconds, unit, suff)
    return res


def format_rate(count, time, unit=None, high_prec=False):
    """Return count / time with reasonable precision."""
    if not time or not count:
        return "0"

    rate = float(count) / float(time)
    if rate >= 1000:
        res = "{}".format(int(round(rate)))
    elif rate >= 100:
        res = "{}".format(round(rate, 1))
    elif rate >= 10:
        res = "{}".format(round(rate, 2))
    else:
        res = "{}".format(round(rate, 3))
    return res


# def format_relative_datetime(dt, as_html=False):
#     """Format a datetime object as relative expression (i.e. '3 minutes ago')."""
#     try:
#         diff = datetime.utcnow() - dt
#         res = None
#         s = diff.seconds

#         if diff.days > 7 or diff.days < 0:
#             res = dt.strftime("%d %b %y")
#         elif diff.days == 1:
#             res = "1 day ago"
#         elif diff.days > 1:
#             res = "{} days ago".format(diff.days)
#         elif s <= 1:
#             res = "just now"
#         elif s < 60:
#             res = "{} seconds ago".format(s)
#         elif s < 120:
#             res = "1 minute ago"
#         elif s < 3600:
#             res = "{} minutes ago".format(s/60)
#         elif s < 7200:
#             res = "1 hour ago"
#         else:
#             res = "{} hours ago".format(s/3600)

#         if as_html:
#             dts = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
#             res = "<span title='{dt}'>{rel}</span>".format(rel=res, dt=dts)

#     except Exception:
#         log_exception("invalid dt: {}".format(dt))
#         res = "(invalid {})".format(dt)
#     return res


# def format_relative_stamp(stamp, as_html=False):
#     dt = stamp_to_datetime(stamp)
#     return format_relative_datetime(dt, as_html)


# def string_to_bool(arg_, default=None):
#     """Return boolean for various bool string representations.

#     Raises Error, if string is not compatible, and no default was passed.
#     """
#     if not default in (None, True, False):
#         raise TypeError("default must be None or boolean")
#     if arg_ is None:
#         if default in (True, False):
#             return default
#         else: #default == None
#             raise ValueError("Argument is %r and default %r." % (arg_, default))
#     else:
#         if arg_ in (True, False):
#             # `bool` is a subclass of `int`, so we get here for 0 and 1 as well!
#             return bool(arg_)
#         arg = arg_.lower().strip()
#         if arg in ("1", "true", "on", "yes"):
#             return True
#         elif arg in ("0", "false", "off", "no"):
#             return False
#         elif default is not None:
#             return default
#     raise ValueError("Argument string is not boolean: %r default: %r." % (arg_, default))


# def byteNumberString(number, thousandsSep=True, partition=False,
#                      base1024=True, appendBytes="iec", prec=0):
#     """Convert bytes into human-readable representation."""
#     magsuffix = ""
#     bytesuffix = ""
#     assert appendBytes in (False, True, "short", "iec")
#     if partition:
#         magnitude = 0
#         if base1024:
#             while number >= 1024:
#                 magnitude += 1
# #                 number = number >> 10
#                 number /= 1024.0
#         else:
#             while number >= 1000:
#                 magnitude += 1
#                 number /= 1000.0
#         # TODO:
#         # Windows 7 Explorer teilt durch 1024, und verwendet trotzdem KB statt KiB.
#         # Außerdem wird aufgerundet: --> 123 -> "1 KB"
#         # http://en.wikipedia.org/wiki/Kibi-#IEC_standard_prefixes
#         magsuffix = ["", "K", "M", "G", "T", "P"][magnitude]
#         if magsuffix:
#             magsuffix = " " + magsuffix

#     if appendBytes:
#         if appendBytes == "iec" and magsuffix:
#             bytesuffix = "iB" if base1024 else "B"
#         elif appendBytes == "short" and magsuffix:
#             bytesuffix = "B"
#         elif number == 1:
#             bytesuffix = " Byte"
#         else:
#             bytesuffix = " Bytes"

#     if thousandsSep and (number >= 1000 or magsuffix):
#         locale.setlocale(locale.LC_ALL, "")
#         # TODO: make precision configurable
#         if prec > 0:
#             fs = "%.{}f".format(prec)
#             snum = locale.format_string(fs, number, thousandsSep)
#         else:
#             snum = locale.format("%d", number, thousandsSep)
#         # Some countries like france use non-breaking-space (hex=a0) as group-
#         # seperator, that's not plain-ascii, so we have to replace the hex-byte
#         # "a0" with hex-byte "20" (space)
#         snum = hexlify(snum).replace("a0", "20").decode("hex")
#     else:
#         snum = str(number)

#     return "%s%s%s" % (snum, magsuffix, bytesuffix)


def lstrip_string(s, prefix, ignore_case=False):
    """Remove leading string from s.

    Note: This is different than `s.lstrip('bar')` which would remove
    all leading 'a', 'b', and 'r' chars.
    """
    if ignore_case:
        if s.lower().startswith(prefix.lower()):
            return s[len(prefix) :]
    else:
        if s.startswith(prefix):
            return s[len(prefix) :]
    return s


# def rstrip_string(s, suffix, ignore_case=False):
#     """Remove trailing string from s.

#     Note: This is different than `s.rstrip('bar')` which would remove
#     all trailing 'a', 'b', and 'r' chars.
#     """
#     if ignore_case:
#         if s.lower().endswith(suffix.lower()):
#             return s[:-len(suffix)]
#     else:
#         if s.endswith(suffix):
#             return s[:-len(suffix)]
#     return s


def progress_bar_str(
    progress: float,
    *,
    width: int = 10,
    level: str = "info",
    border: Union[str, Tuple[str]] = "|",  # ("[", "]"),
    add_percentage: bool = True,
    fill_char: str = " ",
) -> str:
    color_map = {
        "ok": green,
        "warning": yellow,
        "error": red,
    }
    progress = min(1.0, max(0.0, progress))
    real_progress = progress

    if type(border) is str:
        border = (border, border)
    if border:
        width = width - (len(border[0]) - len(border[1]))
    width = max(1, int(width))

    whole_width = math.floor(progress * width)
    remainder_width = (progress * width) % 1
    part_width = math.floor(remainder_width * 8)

    part_char = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"][part_width]
    if (width - whole_width - 1) < 0:
        part_char = ""

    # Very small values should always display a very small bar
    if whole_width < 1 and part_char == " " and progress > 0:
        part_char = "▏"

    line = "█" * whole_width + part_char + fill_char * (width - whole_width - 1)

    if level in color_map:
        line = color_map[level](line)
    if border:
        line = f"{border[0]}{line}{border[1]}"
    if add_percentage:
        p100 = f"{100.0*real_progress:.1f}"
        line += " {: >5}%".format(p100)
    return line


# print(progress_bar_str(0.123))

# print(progress_bar_str(0.123, width=3, border=False))
# print(progress_bar_str(0.023, width=3, border=False))

# print(progress_bar_str(0, width=1, border=False))
# print(progress_bar_str(0.023, width=1, border=False))
# print(progress_bar_str(0.123, width=1, border=False))
# print(progress_bar_str(0.13, width=1, border=False))
# print(progress_bar_str(1.123, width=1, border=False))

# print(progress_bar_str(0, width=3))
# print(progress_bar_str(0.023, width=3))
# print(progress_bar_str(0.123, width=3))
# print(progress_bar_str(0.13, width=3))
# print(progress_bar_str(1.123, width=3))

# print(progress_bar_str(0))
# print(progress_bar_str(0.023))
# print(progress_bar_str(0.123))
# print(progress_bar_str(0.13))
# print(progress_bar_str(1.123))
# raise


def run_process_streamed(
    process,
    name=None,
    on_output=None,
    log_alive=5.0,
    timeout=None,
    poll_interval=0.1,
    flush_min_interval=0.2,
    prefix_chunks=False,
):
    """Read and print output of a running process.


    Args:
        process (subprocess.Popen):
            A running process instance
        name (str):
            Descriptive name of the process
        on_output (stream):
            Call this method for output (default: `logger.info`)
        log_alive (float):
            Print a simple message if not new output was received for X seconds
            (default: 5.0)
        timeout (float):
            Kill process after X seconds (default: None)
        poll_interval (float):
            Poll output buffer every X seconds (default: 0.1)
        flush_min_interval (float):
            Minimal log interval: Wait X seconds for more lines (default: 0.2)
        prefix_chunks (bool):
            Prefix output chunks with <name> (default: False)
    Returns:
        tuple (ret_code, output)

    """
    LINE_PREFIX = " .. "
    out = StringIO()
    pid = process.pid
    if name:
        name = "<{}> {}".format(pid, name)
    else:
        name = "<{}>".format(pid)

    if on_output is None:
        on_output = logger.info

    start = time.time()
    kill_time = start + timeout if timeout else None

    buf_stop_request = Event()
    buf_lock = RLock()
    local_vars = {
        "line_buf": [],
        "last_flush": 0,
        "is_timed_out": False,
    }

    def flush_lines():
        with buf_lock:
            now = time.time()
            elap = now - local_vars["last_flush"]
            line_buf = local_vars["line_buf"]
            local_vars["line_buf"] = []
            # Ignore empty lines
            line_buf = [ln for ln in line_buf if ln.strip()]
            if line_buf:
                # we have something to write, but wait a small duration for more
                if elap < flush_min_interval:
                    return
                line_str = LINE_PREFIX + ("\n" + LINE_PREFIX).join(line_buf)
            elif log_alive:
                # we have nothing to write: print a ping every n seconds
                if local_vars["last_flush"] == 0 or elap < log_alive:
                    return
                line_str = LINE_PREFIX + "<Yabs task running since {}...>".format(
                    format_elap(now - start)
                )
            else:
                return
        local_vars["last_flush"] = now
        if prefix_chunks:
            on_output("process({}) stdout: {}".format(name, line_str))
        else:
            on_output(line_str)
        return

    def flush_handler():
        # logger.debug("flush_handler started...")
        while not buf_stop_request.wait(poll_interval):
            flush_lines()
        # logger.debug("flush_handler stopped.")
        return

    # TODO: only when logger.LEVEL == DEBUG
    flusher = Thread(target=flush_handler, name="Flush process output {}".format(name))
    flusher.start()

    try:
        while process.poll() is None:
            # readline() blocks, so we process it in a separate thread.
            # Read line-by-line
            line = process.stdout.readline()
            line = line.decode()
            out.write(line)
            line = line.replace("\r\n", "\n").rstrip("\n")
            lines = line.split("\n")
            with buf_lock:
                local_vars["line_buf"].extend(lines)

            if kill_time and time.time() > kill_time:
                local_vars["is_timed_out"] = True
                log_warning(
                    "Killing {}... (timeout: {:0.1f} seconds)".format(name, timeout)
                )
                process.kill()
                break
            # logger.debug("run_process_streamed({}) Done.".format(process.pid))
    finally:
        buf_stop_request.set()
        flusher.join()
    flush_lines()

    if local_vars["is_timed_out"]:
        log_error("{} killed (timeout: {:0.1f} seconds)".format(name, timeout))
    return process.returncode, out.getvalue()
