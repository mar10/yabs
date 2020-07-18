# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from pkg_resources import iter_entry_points
from abc import ABC, abstractmethod

# from semantic_version import Version

from .util import check_arg, log_debug, log_info, log_warning, resolve_path


class Plugin(ABC):
    """Base class for plugin wrappers."""
    namespace = None

    def __init__(self, name):
        self.name = name
        self.version = None
        self._plugin = None

    def __str__(self):
        return "{}(v{})@{}".format(self.__class__.__name__, self.name, self.version)

    @abstractmethod
    def run(self):
        pass


class TaskPlugin(Plugin):
    """Base class for yabs task plugin wrappers."""


class PluginManager:
    """
    Maintain a list of plugins.
    """
    plugin_map = {}

    def __init__(self):
        self.namespace = "yabs.tasks"
        self._load_plugins()

    def _load_plugins(self):
        log_info("Load plugins for namespace '{}'...".format(self.namespace))
        for ep in iter_entry_points(group=self.namespace, name=None):
            log_info("Load entry point '{}' {}...".format(ep.name, ep.module_name))
            self.plugin_map[ep.name] = ep.load()
        log_info("map: {}".format(self.plugin_map))

        for name, fn in self.plugin_map.items():
            res = fn()
