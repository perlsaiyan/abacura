from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import Plugin, command


class PluginSession(Plugin):
    """Session specific commands"""
    @command(name="echo")
    def echo(self, text: str):
        """Send text to screen without triggering actions"""
        self.session.output(text, actionable=False)

    @command
    def showme(self, text: str) -> None:
        """Send text to screen as if it came from the socket, triggers actions"""
        self.session.output(text, markup=True)

    @command
    def msdp_command(self, variable: str = '') -> None:
        """Dump MSDP values for debugging"""
        if "REPORTABLE_VARIABLES" not in self.msdp.values:
            self.session.output("[bold red]# MSDPERROR: MSDP NOT LOADED?", markup=True)

        if not variable:
            panel = Panel(Pretty(self.msdp.values), highlight=True)
        else:
            panel = Panel(Pretty(self.msdp.values.get(variable, None)), highlight=True)
        self.session.output(panel, highlight=True, actionable=False)


