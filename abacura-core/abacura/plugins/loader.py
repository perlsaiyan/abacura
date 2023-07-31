from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from datetime import datetime
import importlib
from importlib.util import find_spec
from typing import Dict, TYPE_CHECKING, List, Optional

from textual import log

from abacura.plugins import Plugin

if TYPE_CHECKING:
    pass


@dataclass
class LoadedPlugin:
    plugin: Plugin
    package: str
    package_filename: str
    modified_time: float
    context: Dict


@dataclass
class LoadResult:
    package: str
    package_filename: str
    context: Dict
    exception: Optional[Exception] = None


class PluginLoader:
    """Loads all plugins and registers them"""

    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, LoadedPlugin] = {}
        self.times = {}
        self.total_time = 0
        self.load_failures: list[LoadResult] = []

    def load_package(self, package: str, package_filename: str,
                     plugin_context: Dict, reload: bool = False) -> list[LoadResult]:
        module_start_time = datetime.utcnow()
        context: Dict

        try:
            module = importlib.import_module(package)
            if reload:
                importlib.reload(module)
        except ModuleNotFoundError as exc:
            session = plugin_context['session']
            session.show_exception(exc, msg=f"ERROR LOADING PLUGIN {package}", to_debuglog=True)
            result = LoadResult(package, package_filename, plugin_context, exc)
            self.load_failures.append(result)
            return [result]
        except Exception as exc:
            session = plugin_context['session']
            session.show_exception(exc, msg=f"ERROR LOADING PLUGIN {package}", to_debuglog=True)
            result = LoadResult(package, package_filename, plugin_context, exc)
            self.load_failures.append(result)
            return [result]

        # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
        
        package_results = []

        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and inspect.isclass(cls) and issubclass(cls, Plugin):
                cls._context = plugin_context
                try:
                    plugin_instance: Plugin = cls()
                except Exception as exc:
                    session = plugin_context['session']
                    session.show_exception(exc, msg=f"Error Instantiating {package}.{cls.__name__}", to_debuglog=True)
                    result = LoadResult(package, package_filename, plugin_context, exc)
                    self.load_failures.append(result)
                    continue

                plugin_name = plugin_instance.get_name()
                if plugin_name not in self.plugins:
                    log(f"Adding plugin {name}.{plugin_name}")
                    plugin_instance.director.register_object(plugin_instance)
                    package_file = module.__file__
                    m = os.path.getmtime(package_file)
                    result = LoadResult(package, package_filename, plugin_context, None)
                    self.plugins[plugin_name] = LoadedPlugin(plugin_instance, package, package_file, m, plugin_context)
                    package_results.append(result)
                else:
                    result = LoadResult(package, package_filename, plugin_context, Exception("Duplicate Package"))
                    self.load_failures.append(result)
                    log(f"Skipping duplicate plugin {name}.{plugin_name}")

        elapsed = (datetime.utcnow() - module_start_time).total_seconds()
        mname = module.__name__
        self.times[mname] = self.times.get(mname, 0) + elapsed
        return package_results

    def load_plugins(self, modules: List, plugin_context: Dict) -> list[LoadResult]:
        """Load plugins"""

        start_time = datetime.utcnow()
        plugin_modules = []
        load_results = []

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
            load_results += self.load_package(package, pf, plugin_context)

        end_time = datetime.utcnow()
        self.total_time += (end_time - start_time).total_seconds()
        return load_results

    def reload_package_filename(self, package_filename: str) -> list[LoadResult]:
        # Remove and unregister all plugins in a package

        package_plugins = [(name, lp) for name, lp in self.plugins.items() if lp.package_filename == package_filename]
        if len(package_plugins) == 0:
            log(f"Unable to find context for package {package_filename}")
            return [LoadResult(package_filename, "", {}, Exception(f"Unable to find context for {package_filename}"))]

        # Assume they all have same context and take the first one
        first_lp = package_plugins[0][1]
        context = first_lp.context
        package = first_lp.package

        for name, lp in package_plugins:
            lp.plugin.director.unregister_object(lp.plugin)
            del self.plugins[name]

        # Reload the package
        return self.load_package(package, package_filename, context, reload=True)

    def autoreload_plugins(self) -> list[LoadResult]:
        reload_filenames = set()

        for lp in self.plugins.values():
            if not os.path.exists(lp.package_filename):
                continue

            if os.path.getmtime(lp.package_filename) > lp.modified_time:
                log(f"{lp.package_filename} has been modified, reloading")
                reload_filenames.add(lp.package_filename)

        reload_results: list[LoadResult] = []
        for pf in reload_filenames:
            reload_results += self.reload_package_filename(pf)

        reload_failures = self.load_failures
        self.load_failures = []
        for failure in reload_failures:
            if failure.package_filename in reload_filenames:
                # we already tried to load this
                self.load_failures.append(failure)
                continue

            results = self.load_package(failure.package, failure.package_filename, failure.context, reload=True)
            reload_results += results

        return reload_results

    def reload_plugin_by_name(self, plugin_name: str) -> list[LoadResult]:
        if plugin_name not in self.plugins:
            return [LoadResult(plugin_name, "", {}, Exception(f"No plugin named '{plugin_name}'"))]

        # Get info about the plugin we want to reload
        loaded_plugin = self.plugins[plugin_name]
        result = self.reload_package_filename(loaded_plugin.package_filename)
        return result
