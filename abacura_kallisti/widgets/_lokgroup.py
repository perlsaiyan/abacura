"""Kallisti widget for displaying Group information"""
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static


from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

class LOKGroup(Container):
    """Group information Widget"""

    def __init__(self):
        super().__init__()
        self.display = False
        self.group_title = Static(classes="WidgetTitle")
        self.group_block = Static()

    def on_mount(self):
        self.screen.session.listener(self.update_group)
        self.screen.session.listener(self.update_group_level)

    def compose(self) -> ComposeResult:
        self.styles.height = 9
        yield self.group_title
        yield self.group_block

    @event("msdp_value_GROUP")
    def update_group(self, message: MSDPMessage):
        self.group = message.value

        if self.group:
            self.styles.height = len(self.group) + 1
            self.display = True
            buf = ""
            for g_member in self.group:
                buf += f"{g_member['name']} info\n"
            self.group_block.update(buf)
            return
        
        self.styles.height = len(self.group) + 1
        self.display = False

    @event("msdp_value_GROUPLEVEL")
    def update_group_level(self, message: MSDPMessage):
        self.group_level = message.value
        self.group_title.update(f"Group - Level {self.group_level}")