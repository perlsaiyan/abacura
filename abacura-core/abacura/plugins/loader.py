from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from datetime import datetime
import importlib
from importlib.util import find_spec
from typing import Dict, TYPE_CHECKING, List

from serum import Context
from textual import log

from abacura.plugins import Plugin

if TYPE_CHECKING:
    pass


@dataclass
class LoadedPlugin:
    plugin: Plugin
    package: str
    package_file: str
    modified_time: float
    context: Context


class PluginLoader:
    """Loads all plugins and registers them"""

    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, LoadedPlugin] = {}
        self.times = {}
        self.total_time = 0
        self.failures = []

    def load_package(self, package: str, plugin_context: Context, reload: bool = False):
        module_start_time = datetime.utcnow()
        context: Context

        try:
            module = importlib.import_module(package)
            if reload:
                importlib.reload(module)

        except Exception as exc:
            # TODO: Fix this hack to grab the session, maybe track the failed loads and return a list of failures
            session = plugin_context['session']
            session.show_exception(f"[bold red]# ERROR LOADING PLUGIN {package}:  {repr(exc)}", exc)
            self.failures.append(str(package))
            return

        # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and inspect.isclass(cls) and issubclass(cls, Plugin):
                with plugin_context:
                    plugin_instance: Plugin = cls()

                plugin_name = plugin_instance.get_name()
                if plugin_name not in self.plugins:
                    log(f"Adding plugin {name}.{plugin_name}")
                    plugin_instance.director.register_object(plugin_instance)
                    package_file = module.__file__
                    m = os.path.getmtime(package_file)
                    self.plugins[plugin_name] = LoadedPlugin(plugin_instance, package, package_file, m, plugin_context)
                else:
                    log(f"Skipping duplicate plugin {name}.{plugin_name}")

        elapsed = (datetime.utcnow() - module_start_time).total_seconds()
        mname = module.__name__
        self.times[mname] = self.times.get(mname, 0) + elapsed

    def load_plugins(self, modules: List, plugin_context: Context) -> None:
        """Load plugins"""

        start_time = datetime.utcnow()
        plugin_modules = []

        for mod in modules:
            log.info(f"Loading plugins from {mod}")
            spec = find_spec(mod)
            if not spec:
                continue

            for pathspec in spec.submodule_search_locations:
                for dirpath, _, filenames in os.walk(pathspec):
                    for filename in [f for f in filenames if f.endswith(".py") and not f.startswith('_') and os.path.join(dirpath, f) != __file__]:
                        shortpath = dirpath.replace(pathspec, "") or "/"
                        plugin_modules.append(mod + os.path.join(shortpath, filename))

        # import each one of the modules corresponding to each plugin .py file
        for pf in plugin_modules:
            package = pf.replace(os.sep, ".")[:-3]  # strip .py
            self.load_package(package, plugin_context)

        end_time = datetime.utcnow()
        self.total_time += (end_time - start_time).total_seconds()

    def reload_plugin_by_name(self, plugin_name: str):
        if plugin_name not in self.plugins:
            return

        # Get info about the plugin we want to reload
        loaded_plugin = self.plugins[plugin_name]
        self.reload_package_file(loaded_plugin.package_file)

    def reload_package_file(self, package_file: str):
        # Remove and unregister all plugins in a package

        package_plugins = [(name, lp) for name, lp in self.plugins.items() if lp.package_file == package_file]
        if len(package_plugins) == 0:
            log(f"Unable to find context for package {package_file}")
            return

        # Assume they all have same context and take the first one
        first_lp = package_plugins[0][1]
        context = first_lp.context
        package = first_lp.package
        session = first_lp.plugin.session

        session.output(f"[orange1][italic]> reloading package {package}", markup=True, highlight=True)
        for name, lp in package_plugins:
            lp.plugin.director.unregister_object(lp.plugin)
            del self.plugins[name]

        # Reload the package
        self.load_package(package, context, reload=True)

    def autoreload_plugins(self):
        lp: LoadedPlugin
        package_files = {(lp.package_file, lp.modified_time, lp.plugin.session) for lp in self.plugins.values()}
        reloads = set()
        for pf, modified_time, session in package_files:
            if not os.path.exists(pf):
                continue

            if os.path.getmtime(pf) > modified_time:
                log(f"{pf} has been modified, reloading")
                reloads.add(pf)

        for pf in reloads:
            self.reload_package_file(pf)
