import time
from collections import Counter

from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from abacura.plugins import Plugin, command, CommandError


class PluginSession(Plugin):
    def __init__(self):
        super().__init__()
        if self.session.ring_buffer:
            self.add_ticker(1, self.session.ring_buffer.commit, name="ring-autocommit")

    """Session specific commands"""
    @command(name="echo")
    def echo(self, text: str):
        """Send text to screen without triggering actions"""
        self.session.output(text, actionable=False)

    @command
    def showme(self, text: str) -> None:
        """Send text to screen as if it came from the socket, triggers actions"""
        self.session.output(text, markup=True)

    @command(name="msdp")
    def msdp_command(self, variable: str = '') -> None:
        """Dump MSDP values for debugging"""
        if "REPORTABLE_VARIABLES" not in self.core_msdp.values:
            self.session.output("[bold red]# MSDPERROR: MSDP NOT LOADED?", markup=True)

        if not variable:
            panel = Panel(Pretty(self.core_msdp.values), highlight=True)
        else:
            panel = Panel(Pretty(self.core_msdp.values.get(variable, None)), highlight=True)
        self.session.output(panel, highlight=True, actionable=False)

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

        tbl = Table(title=f" Currently Registered Plugins", title_justify="left")
        tbl.add_column("Type")
        tbl.add_column("Plugin Name")
        tbl.add_column("Description")
        tbl.add_column("Register Actions")
        tbl.add_column("# Actions", justify="right")
        tbl.add_column("# Commands", justify="right")
        tbl.add_column("# Events", justify="right")
        tbl.add_column("# Tickers", justify="right")

        for base, name, doc, indicator, counts in sorted(plugin_rows):
            tbl.add_row(base, name, doc, indicator,
                        str(counts["action"]), str(counts["command"]), str(counts["event"]), str(counts["ticker"]))
        self.output(tbl)
        self.output("\n")

    def show_failures(self):
        if len(self.session.plugin_loader.failures):
            tbl = Table(title="Failed Package Loads", title_justify="left")
            tbl.add_column("Package")
            tbl.add_column("Error")
            for failure in self.session.plugin_loader.failures:
                tbl.add_row(failure.package, failure.error)
            self.output("\n")
            self.output(tbl)

    @command
    def plugins(self, name: str = '') -> None:
        """Get information about plugins"""
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

        tbl = Table(title=f" Details for Plugin {loaded_plugin.package}.{plugin.get_name()}", title_justify="left")
        tbl.add_column("Type")
        tbl.add_column("Name")
        tbl.add_column("Callback")
        tbl.add_column("Details")
        for r in registrations:
            tbl.add_row(r.registration_type, r.name, r.callback.__qualname__, r.details)

        self.output(tbl)

    @command
    def reload(self, plugin_name: str = "", auto: bool = False):
        """Reload plugins"""

        if not plugin_name:
            self.session.plugin_loader.autoreload_plugins()
        else:
            self.session.plugin_loader.reload_plugin_by_name(plugin_name)

        if auto:
            cb = self.session.plugin_loader.autoreload_plugins
            self.output(f"[orange1]> Auto reloading enabled", markup=True, highlight=True)
            self.session.screen.set_interval(interval=1, callback=cb, name="reloadplugins")

    def ring_log_query(self, like: str = "", limit: int = 100, minutes_ago: int = 30,
                       hide_msdp: bool = False, show_commands: bool = False, grouped: bool = False):
        like = like[1:] if len(like) and like[0] == "^" else "%" + like
        like = like[:-1] + "\n" if len(like) and like[-1] == "$" else like + "%"
        # self.session.trace("like: %s" % like)

        ns_ago = int(minutes_ago) * 60 * 1000 * 1000 * 1000
        epoch_start = 0 if not minutes_ago else (time.time_ns() - ns_ago)

        clauses = ["stripped not like '%s%%'" % c for c in "@!&"] if hide_msdp else []

        exclude_commands = ['grep', 'log', 'trace']
        c = ["stripped not like '!&%s%%' and stripped not like '%%@%s%%'" % (cmd, cmd) for cmd in exclude_commands]
        clauses = clauses if show_commands else clauses + c

        clauses = [""] + clauses if len(clauses) else []
        exclude_clause = " and ".join(clauses)

        # self.session.trace("exclude: %s" % exclude_clause)

        # start_ns = time.time_ns()
        logs = self.session.ring_buffer.query(like, clause=exclude_clause, limit=limit,
                                              epoch_start=epoch_start, grouped=grouped)
        # end_ns = time.time_ns()
        # self.session.trace("ringlog: query took %d ms" % ((end_ns - start_ns)/1E6))

        search = like if not grouped else "distinct " + like

        s = f'Searching for {search}: ({len(logs)} matches)\n'

        for log_time, log_context, log_line in logs:
            s += f"\n{log_time:15} {log_context:>6} {log_line:90}"
        self.output(s, actionable=False, loggable=False)

    @command()
    def log(self, like: str = "%", limit: int = 40, minutes_ago: int = 30):
        """Search output log """
        if self.session.ring_buffer is None:
            raise CommandError("No output log ring buffer configured")
        self.ring_log_query(like, limit, hide_msdp=False, minutes_ago=minutes_ago)
