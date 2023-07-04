"""
Various footer widget bits
"""

from textual.reactive import reactive
from textual.widgets import Footer

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import Plugin
from abacura.plugins.events import event

# TODO this should probably be a specific implementation in abacura-kallisti
class AbacuraFooter(Footer):
    """Bottom of screen bar with current session name"""

    session: reactive[str | None] = reactive[str | None]("null")
    level: reactive[str] = reactive[str]("")

    def on_mount(self):
        self.screen.session.director.event_manager.listener(self.update_level)

    def render(self) -> str:
        return f"#{self.session} {self.level}"

    @event("core.msdp.LEVEL", priority=5)
    def update_level(self, message: MSDPMessage):
        """Update reactive values for level"""
        
        self.level = f"Level: {message.value}"
