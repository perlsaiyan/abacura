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
        setattr(self.session, "_lokmsdp", self)

    @command(name="lokmsdp")
    def lok_msdp_command(self, variable: str = '') -> None:
        """Dump MSDP values for debugging"""
        if "REPORTABLE_VARIABLES" not in self._msdp[self.session.name]:
            self.session.output("[bold red]# MSDPERROR: MSDP NOT LOADED?", markup=True)

        if not variable:
            panel = Panel(Pretty(self._msdp[self.session.name]), highlight=True)
        else:
            panel = Panel(Pretty(self._msdp[self.session.name][variable]), highlight=True)

        self.session.output(panel, highlight=True, actionable=False)

    @event("msdp_value")
    def update_lok_msdp(self, message: MSDPMessage):

        if not self.session.name in LOKPlugin._msdp:
            LOKPlugin._msdp[self.session.name] = {}

        if message.type not in LOKPlugin._msdp[self.session.name]:
            LOKPlugin._msdp[self.session.name][message.type] = reactive(message.value)
        else:
            LOKPlugin._msdp[self.session.name][message.type] = message.value

        log(f"Do update on value {message.type} and {message.__dict__}")
