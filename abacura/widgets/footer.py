"""
Various footer widget bits
"""

from textual.reactive import reactive
from textual.widgets import Footer

from abacura.mud.events import event
from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import Plugin

# TODO this should probably be a specific implementation in abacura-kallisti
class AbacuraFooter(Footer):
    """Bottom of screen bar with current session name"""

    session: reactive[str | None] = reactive[str | None]("null")
    level: reactive[str] = reactive[str]("")

    def render(self) -> str:
        return f"#{self.session} {self.level}"

class ScreenPlugin(Plugin):

    # TODO this needs to move to abacura-kallisti as it is mud specific
    @event("msdp_value_LEVEL", priority=5)
    def update_level(self, message: MSDPMessage):
        """Update reactive values for level"""
        
        footer = self.session.screen.query_one(AbacuraFooter)
        footer.level = f"Level: {message.value}"
