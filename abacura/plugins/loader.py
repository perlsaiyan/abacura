from __future__ import annotations

import inspect
import os
from importlib import import_module
from importlib.util import find_spec
from typing import Dict, TYPE_CHECKING

from serum import inject, Context
from textual import log
from textual.widgets import TextLog

from abacura import Config
from abacura.mud.options.msdp import MSDP
from abacura.plugins import Plugin
from abacura.plugins.director import Director

if TYPE_CHECKING:
    from abacura.mud.session import Session


@inject
class PluginLoader(Plugin):
    """Loads all plugins and registers them"""
    config: Config
    sessions: dict
    session: Session
    msdp: MSDP
    director: Director
    tl: TextLog

    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, Plugin] = {}

    def load_plugins(self) -> None:
        """Load plugins"""

        ab_modules = self.config.get_specific_option(self.session.name, "modules")
        if isinstance(ab_modules, list):
            ab_modules.insert(0, "abacura")
        else:
            ab_modules = ["abacura"]

        plugin_modules = []
        for mod in ab_modules:
            log.info(f"Loading plugins from {mod}")
            spec = find_spec(mod)
            for pathspec in spec.submodule_search_locations:
                for dirpath, _, filenames in os.walk(pathspec):
                    for filename in [f for f in filenames if f.endswith(".py") and not f.startswith('_') and os.path.join(dirpath, f) != __file__]:
                        shortpath = dirpath.replace(pathspec, "") or "/"
                        plugin_modules.append(mod + os.path.join(shortpath, filename))

        # TODO: We may want to handle case where we are loading plugins a second time
        self.plugins = {}

        # import each one of the modules corresponding to each plugin .py file
        for pf in plugin_modules:
            package = pf.replace(os.sep, ".")[:-3]  # strip .py

            try:
                module = import_module(package)
            except Exception as exc:
                self.session.output(f"[bold red]# ERROR LOADING PLUGIN {package} (from {pf}): {repr(exc)}",
                                    markup=True, highlight=True)
                continue

            # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
            for name, c in inspect.getmembers(module, inspect.isclass):
                if c.__module__ == module.__name__ and inspect.isclass(c) and issubclass(c, Plugin):
                    with Context(session=self.session, msdp=self.msdp, config=self.config, director=self.director):
                        plugin_instance: Plugin = c()

                    plugin_name = plugin_instance.get_name()
                    log(f"Adding plugin {name}.{plugin_name}")

                    self.plugins[plugin_name] = plugin_instance

                    # Look for listeners in the plugin
                    for member_name, member in inspect.getmembers(plugin_instance, callable):
                        if hasattr(member, 'event_name'):
                            log(f"Appending listener function '{member_name}'")
                            self.session.event_manager.listener(member)
