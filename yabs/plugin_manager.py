# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from inspect import isclass

from pkg_resources import iter_entry_points

from .cmd_build import BuildTask
from .cmd_bump import BumpTask
from .cmd_check import CheckTask
from .cmd_commit import CommitTask
from .cmd_common import WorkflowTask
from .cmd_exec import ExecTask
from .cmd_gh_release import GithubReleaseTask
from .cmd_push import PushTask
from .cmd_pypi_release import PypiReleaseTask
from .cmd_tag import TagTask
from .util import log_debug, log_info, log_warning, logger

# from semantic_version import Version


class PluginManager:
    """
    Load, cache, and maintain a list of plugins and workflow tasks.

    This is basically a singleton.
    """

    #: (str) Entry point group name
    namespace = "yabs.tasks"
    #: (bool) True when all plugin entry points are loaded
    entry_points_searched = False
    #: (bool) True when all plugins' 'register()' method were called.
    plugins_registered = False
    #: (dict) Cached map TASK_NAME => EntryPoint of loaded entry_points
    _entry_point_map = {}
    #: (dict) Cached map TASK_NAME => WorkflowTask of known tasks
    #: Pre-filled with core task classes, and extended by plugins.
    task_class_map = {
        "build": BuildTask,
        "bump": BumpTask,
        "check": CheckTask,
        "commit": CommitTask,
        "exec": ExecTask,
        "github_release": GithubReleaseTask,
        "push": PushTask,
        "pypi_release": PypiReleaseTask,
        "tag": TagTask,
    }

    def __init__(self):
        pass

    @classmethod
    def find_plugins(cls):
        """Load all entry points with group name 'yabs.tasks'."""
        if cls.entry_points_searched:
            return
        cls.entry_points_searched = True
        ep_map = cls._entry_point_map
        log_debug("Search entry points for group '{}'...".format(cls.namespace))

        for ep in iter_entry_points(group=cls.namespace, name=None):
            plugin_name = "{}".format(ep.dist)
            log_debug("Found plugin {} from entry point `{}`".format(plugin_name, ep))

            if ep.name in ep_map:
                log_warning(
                    "Duplicate entry point name: {}; skipping...".format(ep.name)
                )
                continue
            elif ep.name in cls.task_class_map:
                # TODO: support overriding standard tasks?
                # Maybe when 'exreas=[override]' is passed...
                log_warning(
                    "Plugin task name already exists: {}; skipping...".format(ep.name)
                )
                continue

            ep_map[ep.name] = ep

        return

    @classmethod
    def register_plugins(cls):
        if cls.plugins_registered:
            return
        cls.plugins_registered = True

        cls.find_plugins()

        ep_map = cls._entry_point_map
        for name, ep in cls._entry_point_map.items():
            log_info("Load plugin {}...".format(ep.dist))
            try:
                register_fn = ep.load()
                if not callable(register_fn):
                    raise RuntimeError("Entry point {} is not a function".format(ep))
                ep_map[ep.name] = register_fn
            except Exception:
                logger.exception("Failed to load {}".format(ep))

            log_debug("Register plugin {}...".format(ep.dist))
            try:
                plugin = register_fn(task_base=WorkflowTask)
            except Exception:
                logger.exception("Could not register {}".format(name))
                continue
            # Some checks
            if issubclass(plugin, WorkflowTask):
                # Rely on ABC interface
                pass
            elif not isclass(plugin):
                logger.error(
                    "Plugin.register {} did not return a class: {}".format(name, plugin)
                )
            else:
                # Do some interface checks
                if getattr(plugin, "name", None) != name:
                    raise RuntimeError("Plugin must contain `name`")
            cls.task_class_map[name] = plugin
        return

    @classmethod
    def register_cli_commands(cls, subparsers, parents, run_parser):
        # Load entry-point and call register() for plugins.
        cls.register_plugins()
        # We assume that plugins have declared classes that derrived from
        # WorkflowTask
        for task_cls in WorkflowTask.__subclasses__():
            logger.debug("Register {}".format(task_cls))
            task_cls.register_cli_command(subparsers, parents, run_parser)
