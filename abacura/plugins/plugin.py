from abacura.mud import BaseSession
from abacura.plugins import Plugin, action

from importlib import import_module
import inspect
import os
from pathlib import Path

from serum import inject, Context

from textual.app import App
from textual.widgets import TextLog

class PluginHandler():
    def __init__(self, plugin: Plugin):
        super().__init__()
        self.plugin = plugin

    def get_plugin_name(self) -> str:
        return self.plugin.__class__.__name__

    def do(self, line, context):
        self.plugin.do(line, context)

@inject
class PluginManager(Plugin):

    plugins = {}
    plugin_handlers = []
    
    config: dict
    sessions: dict
    session: BaseSession
    app: App
    tl: TextLog

    def __init__(self):
        super().__init__()
        self.load_plugins()

    def handle_command(self, line: str) -> bool:
        """Handles command parsing, returns True if command handled
        so we can pass the command along to something else"""

        cmd = line.split()[0]
        cmd = cmd[1:]

        context = {
            "app": self.app,
            "manager": self
        }

        for p in self.plugin_handlers:
            if p.plugin.get_name() == cmd and p.plugin.plugin_enabled:
                try:
                    self.output(f"[green][italic]> {line}", markup=True, highlight=True)
                    p.do(line, context)
                except Exception as e:
                    self.session.show_exception(
                        f"[bold red] # ERROR: {p.__class__} {p.get_plugin_name()}: {repr(e)}", e
                        )
                return True
        return False       

    def output(self, msg, markup: bool=False, highlight: bool=False) -> None:
        self.tl.markup = markup
        self.tl.markup = highlight
        self.tl.write(msg)

    def load_plugins(self) -> None:
        """Load plugins"""
        framework_path = Path(os.path.realpath(__file__))
        plugin_path = framework_path.parent.parent
        
        plugin_files = [pf for pf in plugin_path.glob('plugins/commands/*.py') if not pf.name.startswith('_')]

        modules = []
        plugins = {}
        handlers = {}

        plugin_list = []
        for path, subdirs, files in os.walk(plugin_path):
            for name in files:
                if not name.startswith("_") and name.endswith(".py"):
                    plugin_list.append(Path(os.path.join(path, name)))
        
        for pf in plugin_list:
            package = str(pf.relative_to(plugin_path.parent)).replace(os.sep, ".")
            package = package[:-3] # strip .py
            try:
                module = import_module(package)
            except Exception as e:
                self.output(f"[bold red]# ERROR LOADING PLUGIN {package} (from {pf}): {repr(e)}", markup=True, highlight=True)
                continue


        for pf in plugin_files:
            package = str(pf.relative_to(plugin_path.parent)).replace(os.sep, ".")
            package = package[:-3] # strip .py
            try:
                module = import_module(package)
            except Exception as e:
                self.output(f"[bold red]# ERROR LOADING PLUGIN {package} (from {pf}): {repr(e)}", markup=True, highlight=True)
                continue

            modules.append(module)
            for name, c in inspect.getmembers(module, inspect.isclass):

                    if c.__module__ == module.__name__ and inspect.isclass(c) and issubclass(c, Plugin):
                        p: Plugin = c()
                        plugins[p.get_name()] = p
                        

                        h = PluginHandler(p)
                        self.plugin_handlers.append(h)
                        handlers[p.get_name()] = h

        self.plugins = plugins

    @action("^Enter your account name. If you do not have an account, just enter a new", "E")
    def action_login(self, command_line: str):
        if self.session.name in self.config and "account_name" in self.config[self.session.name]:
            self.tl.write(self.config[self.session.name]["account_name"])
