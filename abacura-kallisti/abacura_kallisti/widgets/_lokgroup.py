"""Kallisti widget for displaying Group information"""
from collections import OrderedDict
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static, DataTable


from abacura.utils import percent_color
from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

class LOKGroup(Static):
    """Group information Widget"""
    can_focus_children = False

    group = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display = False
        self.expand = True
        
        self.group_title = Static(classes="WidgetTitle")
        self.group_block = DataTable(id="group_detail", zebra_stripes=True, show_header=False, show_row_labels=False, show_cursor=False)
        self.group_block.add_column("ClassLevel", key="classlevel")
        self.group_block.add_column("Name", key="name")
        self.group_block.add_column("H", key="health")
        self.group_block.add_column("M", key="mana")
        self.group_block.add_column("S", key="stam")
        self.group_block.add_column("Flags", key="flags")

    def on_mount(self):
        self.screen.session.add_listener(self.update_group)
        self.screen.session.add_listener(self.update_group_level)

    def compose(self) -> ComposeResult:
        yield self.group_title
        yield self.group_block

    @event("core.msdp.GROUP")
    def update_group(self, message: MSDPMessage):
        def with_color(g):
            buf = "white"
            if g['is_leader'] == "1":
                buf = "bold gold3"
            elif g['is_subleader'] == "1":
                buf = "gold3"
            elif g['class'] in ["TEM", "DRU", "PRO"]:
                buf = "#48D1CC"

            if not g['with_leader'] == "1":
                buf += " italic"

            return f"[{buf}]"

        self.group = message.value
        self.group_block.clear()

        if self.group:
            self.styles.height = len(self.group) + 1
            self.display = True

            for g_member in self.group:
                w_color = with_color(g_member)
                # TODO with LOK/typed MSDP we can drop the int casting here
                row = [
                    f"[{g_member['level']:>3} {g_member['class']}]",
                    f"{w_color}{g_member['name']}",
                    f"[{percent_color(int(g_member['health']))}]{g_member['health']}",
                    f"[{percent_color(int(g_member['mana']))}]{g_member['mana']}",
                    f"[{percent_color(int(g_member['stamina']))}]{g_member['stamina']}",
                    g_member['flags']
                ]
                self.group_block.add_row(*row, label=g_member["name"])
            return
        
        self.display = False

    @event("core.msdp.GROUPLEVEL")
    def update_group_level(self, message: MSDPMessage):
        self.group_level = message.value
        self.group_title.update(f"Group - Level {self.group_level}")