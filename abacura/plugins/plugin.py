from __future__ import annotations

import inspect
import os
from importlib import import_module
from pathlib import Path
from typing import Dict, TYPE_CHECKING

from serum import inject, Context
from textual import log
from textual.app import App
from textual.widgets import TextLog

from abacura import Config
from abacura.plugins import Plugin
from abacura.plugins.registry import TickerRegistry, CommandRegistry, ActionRegistry

if TYPE_CHECKING:
    from abacura.mud.session import Session


@inject
class PluginLoader(Plugin):
    """Loads all plugins and registers them"""
    config: Config
    sessions: dict
    session: Session
    action_registry: ActionRegistry
    command_registry: CommandRegistry
    ticker_registry: TickerRegistry
    app: App
    tl: TextLog

    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, Plugin] = {}

    def load_plugins(self) -> None:
        """Load plugins"""
        framework_path = Path(os.path.realpath(__file__))
        plugin_path = framework_path.parent.parent

        plugin_files = []
        log.debug(f"Loading plugins from {plugin_path} from {__file__}")
        for dirpath, _, filenames in os.walk(plugin_path):
            for filename in [f for f in filenames if f.endswith(".py") and not f.startswith('_') and os.path.join(dirpath, f) != __file__]:
                log(f"Found plugin {os.path.join(dirpath,filename)}")
                plugin_files.append(Path(os.path.join(dirpath, filename)))

        # TODO: We may want to handle case where we are loading plugins a second time
        self.plugins = {}

        # import each one of the modules corresponding to each plugin .py file
        for pf in plugin_files:
            log.debug(f"Loading file {pf}")
            package = str(pf.relative_to(plugin_path.parent.parent)).replace(os.sep, ".")
            package = package[:-3]  # strip .py
            package = package[8:]
            
            try:
                module = import_module(package)
            except Exception as e:
                self.session.output(f"[bold red]# ERROR LOADING PLUGIN {package} (from {pf}): {repr(e)}",
                                    markup=True, highlight=True)
                continue

            # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
            for name, c in inspect.getmembers(module, inspect.isclass):
                if c.__module__ == module.__name__ and inspect.isclass(c) and issubclass(c, Plugin):
                    with Context(app=self.app, loader=self, session=self.session,
                                 action_registry=self.action_registry, command_registry=self.command_registry,
                                 ticker_registry=self.ticker_registry):
                        plugin_instance: Plugin = c()

                    self.action_registry.register_object(plugin_instance)
                    self.command_registry.register_object(plugin_instance)
                    self.ticker_registry.register_object(plugin_instance)

                    plugin_name = plugin_instance.get_name()
                    log(f"Adding plugin {name}.{plugin_name}")

                    self.plugins[plugin_name] = plugin_instance

                    # Look for listeners in the plugin
                    for member_name, member in inspect.getmembers(plugin_instance, callable):
                        if hasattr(member, 'event_name'):
                            log(f"Appending listener function '{member_name}'")
                            self.session.event_manager.listener(member)
