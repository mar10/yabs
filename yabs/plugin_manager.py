# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from inspect import isclass
from pkg_resources import iter_entry_points

# from semantic_version import Version

from .util import log_info, log_warning, logger
from .cmd_common import WorkflowTask


class PluginManager:
    """
    Maintain a list of plugins.
    """

    plugin_map = {}

    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.namespace = "yabs.tasks"
        self._load_plugins()

    def _load_plugins(self):
        handler_map = self.task_manager.handler_map
        log_info("Load plugins for namespace '{}'...".format(self.namespace))

        for ep in iter_entry_points(group=self.namespace, name=None):
            log_info("Load entry point '{}' {}...".format(ep.name, ep.module_name))
            if ep.name in self.plugin_map:
                log_warning(
                    "Duplicate entry point name: {}; skipping...".format(ep.name)
                )
                continue
            if ep.name in handler_map:
                log_warning(
                    "Task name exists in standard: {}; skipping...".format(ep.name)
                )
                continue
            self.plugin_map[ep.name] = ep.load()

        log_info("map: {}".format(self.plugin_map))

        for name, register_fn in self.plugin_map.items():
            try:
                plugin = register_fn(self, WorkflowTask)
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
            handler_map[name] = plugin
