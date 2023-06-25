from rich.panel import Panel
from rich.pretty import Pretty
import time

from abacura.plugins import Plugin, command


class PluginSession(Plugin):
    def __init__(self):
        super().__init__()
        if self.session.ring_buffer:
            self.add_ticker(1, self.session.ring_buffer.commit)

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

    @command
    def plugin(self) -> None:
        """Get information about plugins"""

        self.session.output("Current registered global plugins:")

        for plugin_name, loaded_plugin in self.session.plugin_loader.plugins.items():
            plugin = loaded_plugin.plugin
            indicator = '[bold green]✓' if plugin.plugin_enabled else '[bold red]x'
            self.session.output(
                f"{indicator} [white]{plugin.get_name()}" +
                f" - {plugin.get_help()}", markup=True)

    @command
    def reload(self, plugin_name: str = "", auto: bool = False):
        """Reload plugins"""
        if not plugin_name:
            self.session.plugin_loader.autoreload_plugins()
        else:
            self.session.plugin_loader.reload_plugin_by_name(plugin_name)

        if auto:
            cb = self.session.plugin_loader.autoreload_plugins
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
        for log_time, log_vnum, log_line in logs:
            s += f"\n{log_time:15s} {log_line:90s}"
        self.session.output(s, actionable=False, loggable=False)

    @command()
    def ring_log(self, like: str = "%", limit: int = 40, minutes_ago: int = 30):
        """Search all log entries"""
        if self.session.ring_buffer is None:
            raise ValueError("No ring buffer configured")
        self.ring_log_query(like, limit, hide_msdp=False, minutes_ago=minutes_ago)
