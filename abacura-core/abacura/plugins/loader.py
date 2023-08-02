import inspect
import os
from dataclasses import dataclass, field
from datetime import datetime
import importlib
from importlib.util import find_spec
from typing import Dict, TYPE_CHECKING, List
from collections import Counter

from textual import log

from abacura.plugins import Plugin

if TYPE_CHECKING:
    pass


@dataclass
class PluginModule:
    module_path: str
    absolute_filename: str
    relative_filename: str
    context: Dict = field(default_factory=dict)
    modified_time: float = 0
    plugin_count: int = 0
    last_action: str = ""
    exceptions: list[Exception] = field(default_factory=list)

    @property
    def import_path(self) -> str:
        """Compute the package to import by removing the .py extension and changing path separator to ."""
        name = os.path.splitext(self.relative_filename)[0]
        return name.replace(os.sep, ".")


class PluginLoader:
    """Loads all plugins and registers them"""

    def __init__(self):
        self.module_paths_discovered: Dict[str, Dict] = {}
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_modules: Dict[str, PluginModule] = {}
        self.load_times = Counter()
        self.total_time = 0

    def unload_plugin_module(self, plugin_module: PluginModule):
        """Unregister all plugins loaded from a package"""
        try:
            # put in list to prevent mutation error
            for name, p in list(self.plugins.items()):
                if p._source_filename == plugin_module.absolute_filename:
                    log(f"Unloading/unregistering plugin {name}")
                    p.director.unregister_object(p)
                    self.plugins.pop(name)

            plugin_module.exceptions = []

        except Exception as exc:
            session = plugin_module.context['session']
            session.show_exception(exc, msg=f"ERROR UNLOADING PLUGIN {plugin_module}", to_debuglog=True)
            plugin_module.exceptions.append(exc)

    def load_plugin_module(self, plugin_module: PluginModule, reload: bool = False):
        module_start_time = datetime.utcnow()

        try:
            plugin_module.plugin_count = 0
            plugin_module.exceptions = []
            module = importlib.import_module(plugin_module.import_path)

            if reload:
                importlib.reload(module)
                self.unload_plugin_module(plugin_module)

            self.plugin_modules[plugin_module.absolute_filename] = plugin_module

        except Exception as exc:
            session = plugin_module.context['session']
            session.show_exception(exc, msg=f"ERROR LOADING PLUGIN {plugin_module}", to_debuglog=True)
            plugin_module.exceptions.append(exc)
            return

        # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and inspect.isclass(cls) and issubclass(cls, Plugin):
                cls._context = plugin_module.context
                try:
                    plugin_instance: Plugin = cls()
                    plugin_instance._source_filename = plugin_module.absolute_filename
                except Exception as exc:
                    session = plugin_module.context['session']
                    session.show_exception(exc,
                                           msg=f"Error Instantiating {plugin_module}.{cls.__name__}",
                                           to_debuglog=True)
                    plugin_module.exceptions.append(exc)
                    continue

                plugin_name = plugin_instance.get_name()
                if plugin_name not in self.plugins:
                    log(f"Adding plugin {name}.{plugin_name}")
                    plugin_instance.director.register_object(plugin_instance)
                    plugin_module.plugin_count += 1
                    self.plugins[plugin_name] = plugin_instance
                else:
                    plugin_module.exceptions.append(Exception(f"Duplicate Plugin Name {name}.{plugin_name}"))
                    log(f"Skipping duplicate plugin {name}.{plugin_name}")

        self.load_times[plugin_module.relative_filename] += (datetime.utcnow() - module_start_time).total_seconds()
        return

    def discover_plugin_modules_from_path(self, module_path: str) -> list[PluginModule]:
        discovered = []
        spec = find_spec(module_path)
        if not spec:
            return []

        for pathspec in spec.submodule_search_locations:
            for dirpath, _, filenames in os.walk(pathspec):
                for filename in [f for f in filenames if f.endswith(".py") and not f.startswith('_')]:
                    absolute_filename = os.path.join(dirpath, filename)
                    if absolute_filename == __file__:
                        continue

                    relative_path = os.path.relpath(dirpath, pathspec)
                    if dirpath == pathspec:
                        relative_path = ""
                    relative_filename = os.path.join(module_path, relative_path, filename)
                    mtime = os.path.getmtime(absolute_filename)
                    pm = PluginModule(module_path, absolute_filename, relative_filename, modified_time=mtime)
                    discovered.append(pm)

        return discovered

    def load_plugins(self, module_paths: List[str], plugin_context: Dict) -> list[PluginModule]:
        """Load/Reload plugins from module_paths"""

        start_time = datetime.utcnow()

        load_results = []

        for module_path in module_paths:
            self.module_paths_discovered[module_path] = plugin_context
            log.info(f"Loading plugins from {module_path}")

            current = [pm for pm in self.plugin_modules.values() if pm.module_path == module_path]
            discovered = self.discover_plugin_modules_from_path(module_path)

            for plugin_module in discovered:
                reload = False
                if plugin_module.absolute_filename in self.plugin_modules:
                    reload = True
                    existing_module = self.plugin_modules[plugin_module.absolute_filename]
                    if existing_module.modified_time != plugin_module.modified_time:
                        log(f"{plugin_module.absolute_filename} has been modified, reloading")
                    elif len(existing_module.exceptions) > 0:
                        log(f"{plugin_module.absolute_filename} has errors, reloading")
                    elif existing_module.context != plugin_context:
                        log(f"{plugin_module.absolute_filename} context changed, reloading")
                    else:
                        # nothing changed, don't load
                        continue

                plugin_module.context = plugin_context
                plugin_module.last_action = "reloaded" if reload else "loaded"
                self.load_plugin_module(plugin_module, reload=reload)
                load_results.append(plugin_module)

            # remove separately so we don't mutate the list in the iterator above
            discovered_files = {pm.absolute_filename for pm in discovered}
            removed = [pm for pm in current if pm.absolute_filename not in discovered_files]

            for plugin_module in removed:
                log(f"{plugin_module.absolute_filename} does not exist, removing")
                self.unload_plugin_module(plugin_module)
                self.plugin_modules.pop(plugin_module.absolute_filename)
                plugin_module.last_action = "unloaded"
                load_results.append(plugin_module)

        self.total_time += (datetime.utcnow() - start_time).total_seconds()
        return load_results

    def reload_plugins(self) -> list[PluginModule]:
        results: list[PluginModule] = []
        for module_path, context in self.module_paths_discovered.items():
            results += self.load_plugins([module_path], context)
        return results

    def get_failed_modules(self) -> list[PluginModule]:
        return [m for m in self.plugin_modules.values() if len(m.exceptions)]
