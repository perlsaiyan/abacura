from abacura.plugins import Plugin

from importlib import import_module
import inspect
import os
from pathlib import Path
from typing import Optional
from abacura.mud.session import Session
from textual.app import App

class PluginHandler():
    def __init__(self, plugin: Plugin):
        super().__init__()
        self.plugin = plugin

    def get_plugin_name(self) -> str:
        return self.plugin.__class__.__name__

    def do(self, line, context):
        self.plugin.do(line, context)


class PluginManager(Plugin):

    plugins = {}
    plugin_handlers = []

    def __init__(self, app: App, name: str, session: Optional[Session]):
        super().__init__()
        self.name = name
        self.app = app
        self.session = session

    def handle_command(self, line: str) -> bool:
        """Handles command parsing, returns True if command handled
        so we can pass the command along to something else"""

        cmd = line.split()[0]
        cmd = cmd[1:]

        context = {
            "session": self.session,
            "app": self.app,
            "manager": self
        }

        for p in self.plugin_handlers:
            if p.plugin.get_name() == cmd and p.plugin.plugin_enabled:
                try:
                    p.do(line, context)
                except Exception as e:
                    self.app.handle_mud_data(self.app.session, f"[bold red] # ERROR: {p.get_plugin_name()}: {repr(e)}")
                return True
        return False       

    def output(self, msg):
        self.app.handle_mud_data(self.session, msg)

    def load_plugins(self) -> None:
        """Load plugins"""
        framework_path = Path(os.path.realpath(__file__))
        plugin_path = framework_path.parent.parent
        plugin_files = [pf for pf in plugin_path.glob('*/*/**/*.py') if not pf.name.startswith('_')]

        modules = []
        plugins = {}
        handlers = {}

        for pf in plugin_files:
            package = str(pf.relative_to(plugin_path.parent)).replace(os.sep, ".")
            package = package[:-3] # strip .py
            module = import_module(package)
            modules.append(module)
            for name, c in inspect.getmembers(module, inspect.isclass):
                if c.__module__ == module.__name__ and inspect.isclass(c) and issubclass(c, Plugin):
                    p: Plugin = c()
                    plugins[p.get_name()] = p
                    #self.app.handle_mud_data(self.app.session,f"[bold red]# loading {p.get_name()}")

                    h = PluginHandler(p)
                    self.plugin_handlers.append(h)
                    handlers[p.get_name()] = h

        #self.app.handle_mud_data(self.app.session,f"[bold red]# Loaded {len(plugins)} plugins and {len(self.plugin_handlers)} handlers")
        self.plugins = plugins
