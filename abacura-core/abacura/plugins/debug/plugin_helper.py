from collections import Counter

from rich.text import Text

from abacura.plugins import Plugin, command
from abacura.utils.renderables import tabulate, AbacuraPanel, AbacuraError


class PluginHelper(Plugin):
    """Provides #plugin command"""

    def show_all_plugins(self):
        plugin_rows = []

        for name, loaded_plugin in self.session.plugin_loader.plugins.items():
            plugin = loaded_plugin.plugin
            registrations = self.director.get_registrations_for_object(plugin)
            counts = Counter([r.registration_type for r in registrations])

            base = plugin.__class__.__base__.__name__
            indicator = '✓' if plugin.register_actions else 'x'
            indicator_color = "bold green" if plugin.register_actions else 'bold red'
            plugin_rows.append((base, plugin.get_name(), plugin.get_help() or '',
                                Text(indicator, style=indicator_color), counts))

        rows = []
        for base, name, doc, indicator, counts in sorted(plugin_rows):
            rows.append((base, name, doc, indicator,
                         counts["action"], counts["commands"], counts["event"], counts["ticker"]))
        tbl = tabulate(rows, headers=["Type", "Name", "Description", "Register Actions",
                                      "# Actions", "# Commands", "# Events", "# Tickers"])
        self.output(AbacuraPanel(tbl, title="Loaded Plugins"))

    def show_failures(self):
        if len(self.session.plugin_loader.load_failures):
            rows = [(f.package, f.error) for f in self.session.plugin_loader.load_failures]
            tbl = tabulate(rows, headers=["Filename", "Error"])
            self.output(AbacuraError(tbl, title="Failed Package Loads", warning=True))

    @command
    def plugins(self, name: str = '') -> None:
        """
        Get information about plugins

        :param name: Show details about a single plugin, leave blank to list all
        """
        if not name:
            self.show_all_plugins()
            self.show_failures()
            return

        loaded_plugins = self.session.plugin_loader.plugins
        matches = [n for n in loaded_plugins.keys() if n.lower().startswith(name.lower())]
        exact = [n for n in loaded_plugins.keys() if n.lower() == name.lower()]

        if len(exact) == 1:
            matches = exact
        elif len(matches) > 1:
            self.output(f"[orange1] Ambiguous Plugin Name: {matches}", markup=True)
            return
        elif len(matches) == 0:
            self.output(f"[orange1] No plugin by that name [{name}]", markup=True)
            return

        loaded_plugin = loaded_plugins[matches[0]]
        plugin = loaded_plugin.plugin

        registrations = self.director.get_registrations_for_object(plugin)

        rows = []
        for r in registrations:
            rows.append((r.registration_type, r.name, r.callback.__qualname__, r.details))

        tbl = tabulate(rows, headers=["Type", "Name", "Callback", "Details"], title=f"Registered Callbacks")

        self.output(AbacuraPanel(tbl, title=f"{loaded_plugin.package}.{plugin.get_name()}"))

    @command
    def reload(self, plugin_name: str = ""):
        """
        Reload plugins

        :param plugin_name: Reload a specific plugin, leave blank to load all changed files
        """

        if not plugin_name:
            results = self.session.plugin_loader.autoreload_plugins()
        else:
            results = self.session.plugin_loader.reload_plugin_by_name(plugin_name)

        rows = []
        for result in results:
            s = "[green]Success" if result.exception is None else "[red]Failure"
            rows.append((result.package_filename, s, str(result.exception)))

        if len(rows):
            tbl = tabulate(rows, headers=["Plugin Filename", "Result", "Error"])
        else:
            tbl = Text("No plugins reloaded.")

        self.output(AbacuraPanel(tbl, title="Reload Results"))
