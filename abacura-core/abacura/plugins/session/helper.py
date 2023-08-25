import time

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPanel


class SessionHelper(Plugin):
    """Provides commands related to the session"""
    def __init__(self):
        super().__init__()
        if self.session.ring_buffer:
            self.add_ticker(1, self.session.ring_buffer.commit, name="ring-autocommit")

    """Session specific commands"""
    @command(name="echo")
    def echo(self, text: str):
        """
        Send text to the output window without triggering actions

        Use #showme to trigger actions

        :param text: The text to send to the output window
        """
        self.session.output(text, actionable=False)

    @command
    def showme(self, text: str) -> None:
        """
        Send text to the output window and trigger actions

        Use #echo to avoid triggering actions

        :param text: The text to send to the output window / trigger actions
        """
        self.session.output(text, markup=True)

    @command(name="msdp")
    def msdp_command(self, variable: str = '') -> None:
        """
        Dump MSDP values for debugging

        :param variable: The name of a variable to view, leave blank for all
        """
        if "REPORTABLE_VARIABLES" not in self.core_msdp.values:
            raise CommandError("MSDP not loaded")

        if not variable:
            panel = Panel(Pretty(self.core_msdp.values), highlight=True)
        else:
            panel = Panel(Pretty(self.core_msdp.values.get(variable, None)), highlight=True)
        self.session.output(panel, highlight=True, actionable=False)

    @command(name="workers")
    def workers(self, group: str = ""):
        """
        Show all workers or for optional group

        :param group: Show workers for this group only
        """

        title = "Running Workers"
        title += "" if group == "" else f" in Group '{group}'"

        rows = []
        for worker in filter(lambda x: group == "" or group == x.group, self.session.abacura.workers):
            rows.append((worker.group, worker.name, worker.description))

        tbl = tabulate(rows, headers=["Group", "Name", "Description"])
        self.output(AbacuraPanel(tbl, title=title), actionable=False, highlight=True)
