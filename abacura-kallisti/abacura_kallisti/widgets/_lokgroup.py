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
            if g.get('is_leader') == "1":
                buf = "bold gold3"
            elif g.get('is_subleader') == "1":
                buf = "gold3"
            elif g.get('cls') in ["TEM", "DRU", "PRO"]:
                buf = "#48D1CC"

            if not g.get('with_leader') == "1":
                buf += " italic"

            return f"[{buf}]"

        self.group = message.value
        self.group_block.clear()

        # Debug: Log the group data
        log.info(f"Group data received: {len(self.group) if self.group else 0} members")
        if self.group:
            for i, member in enumerate(self.group):
                log.info(f"Member {i}: {member.get('name', 'Unknown')} - {member.get('class', 'Unknown')} {member.get('level', 'Unknown')}")

        if self.group:
            # Set height to accommodate title + all group members + some padding
            self.styles.height = len(self.group) + 2
            self.display = True

            for g_member in self.group:
                w_color = with_color(g_member)
                # Use the correct field names from the data structure
                level = g_member.get('level', 0)
                cls = g_member.get('class', '')
                name = g_member.get('name', '')
                health = g_member.get('health', 0)
                mana = g_member.get('mana', 0)
                stamina = g_member.get('stamina', 0)
                flags = g_member.get('flags', '')
                
                row = [
                    f"[{level:>3} {cls}]",
                    f"{w_color}{name}",
                    f"[{percent_color(int(health))}]{health}",
                    f"[{percent_color(int(mana))}]{mana}",
                    f"[{percent_color(int(stamina))}]{stamina}",
                    flags
                ]
                self.group_block.add_row(*row, label=name)
            return
        
        self.display = False

    @event("core.msdp.GROUPLEVEL")
    def update_group_level(self, message: MSDPMessage):
        self.group_level = message.value
        self.group_title.update(f"Group - Level {self.group_level}")