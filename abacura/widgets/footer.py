from abacura.mud.events import event, AbacuraMessage
from abacura.plugins import Plugin, command
from textual import log
from rich.pretty import Pretty
from textual.reactive import reactive
from textual.widgets import Footer
from abacura.mud.options.msdp import MSDPMessage

class AbacuraFooter(Footer):
    """Bottom of screen bar with current session name"""

    session: reactive[str | None] = reactive[str | None]("null")
    level: reactive[str] = reactive[str]("")

    def render(self) -> str:
        return f"#{self.session} {self.level}"

class ScreenPlugin(Plugin):

    @event("msdp_value_LEVEL", priority=5)
    def update_level(self, message: AbacuraMessage):
        """REACTIVE UPDATES"""
        
        footer = self.session.screen.query_one(AbacuraFooter)
        footer.level = f"Level: {message.value}"

    @command(name="poo")
    def poo(self):
        pass