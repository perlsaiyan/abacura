"""Kallisti widget for displaying Group information"""
from collections import OrderedDict
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static, DataTable


from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

class LOKGroup(Static):
    """Group information Widget"""

    group = []
    pct_colors = OrderedDict()
    pct_colors[80] = "green"
    pct_colors[60] = "green_yellow"
    pct_colors[40] = "yellow"
    pct_colors[20] = "dark_orange3"
    pct_colors[0]  = "red"

    def __init__(self):
        super().__init__()
        self.display = False
        self.group_title = Static(classes="WidgetTitle")
        self.group_block = DataTable(id="aff_detail", zebra_stripes=True, show_header=False, show_row_labels=False, show_cursor=False)
        self.group_block.add_column("ClassLevel", key="classlevel")
        self.group_block.add_column("Name", key="name")
        self.group_block.add_column("H", key="health")
        self.group_block.add_column("M", key="mana")
        self.group_block.add_column("S", key="stam")
        self.group_block.add_column("Flags", key="flags")

    def on_mount(self):
        self.screen.session.listener(self.update_group)
        self.screen.session.listener(self.update_group_level)

    def compose(self) -> ComposeResult:
        self.styles.height = 9
        yield self.group_title
        yield self.group_block

    def pct_color(self,c) -> str:
        cval = int(c)
        for key, value in self.pct_colors.items():
            if key < cval:
                return value
        return ""
    
    @event("core.msdp.GROUP")
    def update_group(self, message: MSDPMessage):
        def with_color(g):
            buf = "white"
            if g['is_leader'] == "1":
                buf = "bold gold3"
            elif g['is_subleader'] == "1":
                buf = "gold3"

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
                row = [
                    f"[{g_member['level']:>3} {g_member['class']}]",
                    f"{w_color}{g_member['name']}",
                    f"[{self.pct_color(g_member['health'])}]{g_member['health']}",
                    f"[{self.pct_color(g_member['mana'])}]{g_member['mana']}",
                    f"[{self.pct_color(g_member['stamina'])}]{g_member['stamina']}",
                    g_member['flags']
                ]
                self.group_block.add_row(*row, label=g_member["name"])
            return
        
        self.styles.height = len(self.group) + 1
        self.display = False

    @event("core.msdp.GROUPLEVEL")
    def update_group_level(self, message: MSDPMessage):
        self.group_level = message.value
        self.group_title.update(f"Group - Level {self.group_level}")