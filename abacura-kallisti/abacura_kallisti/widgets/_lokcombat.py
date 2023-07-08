"""Kallisti widget for displaying Combat information"""
from collections import OrderedDict

from rich.segment import Segment
from rich.style import Style
from textual import log
from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.reactive import reactive
from textual.strip import Strip
from textual.widgets import Static, DataTable


from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

class LOKCombatTop(DataTable):
    c_position: reactive[str] = reactive("Standing")
    c_alignment: reactive[str] = reactive("")

    def on_mount(self):
        self.show_header = False
        self.show_cursor = False
        self.show_row_labels = False
        self.add_columns("pos", "align")
        self.update()

    def update(self):
        self.clear()
        self.add_row(self.c_position, self.c_alignment)

class LOKCombatStatus(DataTable):
    c_ac: reactive[int] = reactive(0)
    c_damroll: reactive[int] = reactive(0)
    c_hitroll: reactive[int] = reactive(0)
    c_wimpy: reactive[int] = reactive(0)
    c_hunger: reactive[int] = reactive(0)
    c_thirst: reactive[int] = reactive(0)
    c_hp: reactive[str] = reactive("?%")
    c_mp: reactive[str] = reactive("?%")
    c_sp: reactive[str] = reactive("?%")

    def on_mount(self):
        self.show_header = False
        self.show_cursor = False
        self.show_row_labels = False
        self.add_columns("r1","r2","r3","r4","r5","r6")
        self.update()

    def update(self):
        self.clear()
        self.add_row("[cyan] AC:",f"[white]{self.c_ac}","[cyan]Dam:",f"[white]{self.c_damroll}", "[cyan]Hit:", f"[white]{self.c_hitroll}")
        self.add_row("[cyan]Wmp:",f"[white]{self.c_wimpy}","[cyan]Hun:",f"[white]{self.c_hunger}", "[cyan]Thi:", f"[white]{self.c_thirst}")
        self.add_row("[cyan] HP:",f"[white]{self.c_hp}","[cyan] MP:",f"[white]{self.c_mp}", "[cyan] SP:", f"[white]{self.c_sp}")

class LOKCombat(Static):
    """Combat information Widget"""

    can_focus_children = False
    c_ac = 0
    c_damroll = 0
    c_hitroll = 0
    c_wimpy = 0

    c_health = 0
    c_mana = 0
    c_stam = 0

    c_mount = ""
    c_mount_health = 0
    c_mount_mana = 0
    c_mount_stam = 0

    c_opponent_name = ""
    c_opponent_number = 0
    c_opponent_health = 0
    c_opponent_stam = 0

    my_reactives = {
        'POSITION': "c_position",
        'ALIGNMENT': "c_alignment",
        'WIELD': "c_wield",
        'HELD' : "c_held",
        'SHIELD': "c_shield",
        "QUICKDRAW": "c_quick",
        "AC": "c_ac",
        "DAMROLL": "c_damroll",
        "HITROLL": "c_hitroll",
        "WIMPY": "c_wimpy",
        "MOUNT_NAME": "c_mount",
        "OPPONENT_NAME": "c_opponent_name"
    }

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.combat_title = Static("Combat",classes="WidgetTitle")
        self.combat_top = LOKCombatTop()
        self.combat_stats = LOKCombatStatus()
        self.wield = Static("[cyan]Wld:")
        self.held = Static("[cyan]Hld:")
        self.shield = Static("[cyan]Shi:")
        self.quick = Static("[cyan]Qck:")

    def on_mount(self):
        self.screen.session.listener(self.update_combat_values)

    def compose(self) -> ComposeResult:
        yield self.combat_title
        yield self.combat_top
        yield Static()
        yield self.wield
        yield self.held
        yield self.shield
        yield self.quick
        yield Static()
        yield self.combat_stats

    @event("core.msdp")
    def update_combat_values(self, msg: MSDPMessage):
        if msg.subtype == "POSITION":
            self.combat_top.c_position = msg.value
            self.combat_top.update()
        elif msg.subtype == "ALIGNMENT":
            v = int(msg.value)
            if v > 700:
                self.combat_top.c_alignment = f"[bold bright_white] Good ({msg.value})"
            elif v > 350:
                self.combat_top.c_alignment = f"[bright_white] Good ({msg.value})"
            elif v > 0:
                self.combat_top.c_alignment = f"[white] Neutral ({msg.value})"
            elif v > -350:
                self.combat_top.c_alignment = f"[bright_black] Neutral ({msg.value})"
            elif v > -700:
                self.combat_top.c_alignment = f"[red] Evil ({msg.value})"
            else:
                self.combat_top.c_alignment = f"[bold red] Evil ({msg.value})"

        elif msg.subtype == "WIELD":
            self.wield.update(f"[cyan]Wld: [white]{msg.value}")
        elif msg.subtype == "HOLD":
            self.held.update(f"[cyan]Hld: [white]{msg.value}")
        elif msg.subtype == "SHIELD":
            self.shield.update(f"[cyan]Shi: [white]{msg.value}")
        elif msg.subtype == "QUICKDRAW":
            self.quick.update(f"[cyan]Qck: [white]{msg.value}")

        elif msg.subtype == "AC":
            self.combat_stats.c_ac = int(msg.value)
            self.combat_stats.update()
        elif msg.subtype == "DAMROLL":
            self.combat_stats.c_damroll = int(msg.value)
            self.combat_stats.update()
        elif msg.subtype == "HITROLL":
            self.combat_stats.c_hitroll = int(msg.value)
            self.combat_stats.update()            