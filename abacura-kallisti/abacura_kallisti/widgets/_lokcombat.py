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

from abacura.utils import percent_color
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
    c_hp: reactive[str] = reactive("?")
    c_mp: reactive[str] = reactive("?")
    c_sp: reactive[str] = reactive("?")

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

    c_mount_name = ""
    c_mount_health = 100
    c_mount_health_max = 100
    c_mount_stamina = 100
    c_mount_stamina_max = 100

    c_opponent_name = ""
    c_opponent_number = 0
    c_opponent_health = 0
    c_opponent_health_max = 0
    c_opponent_stamina = 0
    c_opponent_stamina_max = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.combat_title = Static("Combat",classes="WidgetTitle")
        self.combat_top = LOKCombatTop()
        self.combat_stats = LOKCombatStatus()
        self.wield = Static("[cyan]Wld:")
        self.held = Static("[cyan]Hld:")
        self.shield = Static("[cyan]Shi:")
        self.quick = Static("[cyan]Qck:")
        self.mount_name = Static("[cyan]Mount:")
        self.mount_block = DataTable(show_header=False,show_cursor=False, show_row_labels=False)
        self.mount_block.add_columns("H","hval","S","sval")
        self.opponent_name = Static("[cyan]Opp:")
        self.opponent_block = DataTable(show_header=False,show_cursor=False, show_row_labels=False)
        self.opponent_block.add_columns("H","hval","S","sval")

    def on_mount(self):
        self.screen.session.add_listener(self.update_combat_values)

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
        yield self.mount_name
        yield self.mount_block
        yield self.opponent_name
        yield self.opponent_block

    def healthpct(self, health: int = 0):
        if self.screen:
            max = int(self.screen.session.core_msdp.values.get("HEALTH_MAX",health))
            if max > 0:
                pct = int(health * 100 / max)
                return f"[{percent_color(pct)}]{pct}%"
        return "0%"

    def manapct(self, mana: int = 0):
        if self.screen:
            max = int(self.screen.session.core_msdp.values.get("MANA_MAX",mana))
            if max > 0:
                pct = int(mana * 100 / max)
                return f"[{percent_color(pct)}]{pct}%"
        return "0%"

    def stampct(self, stam: int = 0):
        if self.screen:
            max = int(self.screen.session.core_msdp.values.get("STAMINA_MAX",stam))
            if max > 0:
                pct = int(stam * 100 / max)
                return f"[{percent_color(pct)}]{pct}%"
        return "0%"

    def mount_block_update(self):
        self.mount_block.clear()
        if self.c_mount_name != "":
            if self.c_mount_health_max == 0:
                self.c_mount_health_max = 100
            if self.c_mount_stamina_max == 0:
                self.c_mount_stamina_max = 100

            hpct = int(self.c_mount_health * 100/ self.c_mount_health_max)
            spct = int(self.c_mount_stamina * 100/ self.c_mount_stamina_max)

            self.mount_block.add_row(
                "[cyan] HP:",
                f"[{percent_color(hpct)}]{hpct}%"
                "[cyan] SP:",
                f"[{percent_color(spct)}]{spct}%"
            )


    def opponent_block_update(self):
        self.opponent_block.clear()
        if self.c_opponent_name != "":
            if self.c_opponent_health_max == 0:
                self.c_opponent_health_max = 100
            if self.c_opponent_stamina_max == 0:
                self.c_opponent_stamina_max = 100

            if self.c_opponent_health_max > 0:
                hpct = int(self.c_opponent_health * 100/ self.c_opponent_health_max)
            else:
                hpct = 0
            
            if self.c_opponent_stamina_max > 0:
                spct = int(self.c_opponent_stamina * 100/ self.c_opponent_stamina_max)
            else:
                spct = 0

            self.opponent_block.add_row(
                "[cyan] HP:",
                f"[{percent_color(hpct)}]{hpct}%"
                "[cyan] SP:",
                f"[{percent_color(spct)}]{spct}%"
            )
        else:
            self.opponent_block.add_row("", "", "",  "")

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

        elif msg.subtype == "WIMPY":
            self.combat_stats.c_wimpy = int(msg.value)
            self.combat_stats.update()
        elif msg.subtype == "HUNGER":
            self.combat_stats.c_hunger = int(msg.value)
            self.combat_stats.update()
        elif msg.subtype == "THIRST":
            self.combat_stats.c_thirst = int(msg.value)
            self.combat_stats.update()

        elif msg.subtype == "HEALTH":
            self.combat_stats.c_hp = self.healthpct(int(msg.value))
            self.combat_stats.update()
        elif msg.subtype == "MANA":
            self.combat_stats.c_mp = self.manapct(int(msg.value))
            self.combat_stats.update()
        elif msg.subtype == "STAMINA":
            self.combat_stats.c_sp = self.stampct(int(msg.value))
            self.combat_stats.update()

        elif msg.subtype == "MOUNT_NAME":
            self.c_mount_name = msg.value
            self.mount_name.update(f"\n[cyan] Mnt: [white]{msg.value}")
            self.mount_block_update()
        elif msg.subtype == "MOUNT_HEALTH":
            self.c_mount_health = int(msg.value)
            self.mount_block_update()
        elif msg.subtype == "MOUNT_HEALTH_MAX":
            self.c_mount_health_max = int(msg.value)
            self.mount_block_update()
        elif msg.subtype == "MOUNT_STAMINA":
            self.c_mount_stamina = int(msg.value)
            self.mount_block_update()
        elif msg.subtype == "MOUNT_STAMINA_MAX":
            self.c_mount_stamina_max = int(msg.value)
            self.mount_block_update()

        elif msg.subtype == "OPPONENT_NAME":
            self.c_opponent_name = msg.value
            self.opponent_name.update(f"\n[cyan] Opp: [white]{msg.value}")
            self.opponent_block_update()
        elif msg.subtype == "OPPONENT_HEALTH":
            self.c_opponent_health = int(msg.value)
            self.opponent_block_update()
        elif msg.subtype == "OPPONENT_HEALTH_MAX":
            self.c_opponent_health_max = int(msg.value)
            self.opponent_block_update()
        elif msg.subtype == "OPPONENT_STAMINA":
            self.c_opponent_stamina = int(msg.value)
            self.opponent_block_update()
        elif msg.subtype == "OPPONENT_STAMINA_MAX":
            self.c_opponent_stamina_max = int(msg.value)
            self.opponent_block_update()
