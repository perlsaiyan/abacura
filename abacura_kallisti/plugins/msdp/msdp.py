"""LOK MSDP plugis"""
from __future__ import annotations

from rich.panel import Panel
from rich.pretty import Pretty
from textual import log
from textual.reactive import reactive

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event
from abacura.plugins import command
from abacura_kallisti.plugins import LOKPlugin


# TODO: disable the abacura @msdp command and let's implement it here
class LOKMSDP(LOKPlugin):

    def __init__(self):
        super().__init__()

    @command(name="lokmsdp")
    def lok_msdp_command(self, variable: str = '') -> None:
        """Dump MSDP values for debugging"""
        if "REPORTABLE_VARIABLES" not in self.msdp.values:
            self.session.output("[bold red]# MSDPERROR: MSDP NOT LOADED?", markup=True)

        if not variable:
            panel = Panel(Pretty(self.msdp.values), highlight=True)
        else:
            panel = Panel(Pretty(self.msdp.values[variable]), highlight=True)

        self.session.output(panel, highlight=True, actionable=False)

    @event("msdp_value")
    def update_lok_msdp(self, message: MSDPMessage):
        self.msdp.values[message.type] = message.value
