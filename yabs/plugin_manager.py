# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from inspect import isclass

from pkg_resources import iter_entry_points

from .task.build import BuildTask
from .task.bump import BumpTask
from .task.check import CheckTask
from .task.commit import CommitTask
from .task.common import WorkflowTask
from .task.exec import ExecTask
from .task.github_release import GithubReleaseTask
from .task.push import PushTask
from .task.pypi_release import PypiReleaseTask
from .task.tag import TagTask
from .task.winget_release import WingetReleaseTask
from .util import log_debug, log_warning, logger

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
        "winget_release": WingetReleaseTask,
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
        log_debug(f"Search entry points for group '{cls.namespace}'...")

        for ep in iter_entry_points(group=cls.namespace, name=None):
            plugin_name = f"{ep.dist}"
            log_debug(f"Found plugin {plugin_name} from entry point `{ep}`")

            if ep.name in ep_map:
                log_warning(f"Duplicate entry point name: {ep.name}; skipping...")
                continue
            elif ep.name in cls.task_class_map:
                # TODO: support overriding standard tasks?
                # Maybe when 'exreas=[override]' is passed...
                log_warning(f"Plugin task name already exists: {ep.name}; skipping...")
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
            log_debug(f"Load plugin {ep.dist}...")
            try:
                register_fn = ep.load()
                if not callable(register_fn):
                    raise RuntimeError(f"Entry point {ep} is not a function.")
                ep_map[ep.name] = register_fn
            except Exception:
                logger.exception(f"Failed to load {ep}.")

            log_debug(f"Register plugin {ep.dist}...")
            try:
                plugin = register_fn(task_base=WorkflowTask)
            except Exception:
                logger.exception(f"Could not register {name}")
                continue
            # Some checks
            if issubclass(plugin, WorkflowTask):
                # Rely on ABC interface
                pass
            elif not isclass(plugin):
                logger.error(f"Plugin.register {name} did not return a class: {plugin}")
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
            logger.debug(f"Register {task_cls}")
            task_cls.register_cli_command(subparsers, parents, run_parser)
