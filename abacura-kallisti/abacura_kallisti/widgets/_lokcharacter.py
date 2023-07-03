from __future__ import annotations

from typing import TYPE_CHECKING

from textual import log
from textual.app import ComposeResult, RenderResult
from textual.reactive import reactive
from textual.widgets import Static

import rich.box as box
from rich.pretty import Pretty
from rich.table import Table

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

if TYPE_CHECKING:
    from abacura import Session
    from abacura_kallisti.screens import BetterKallistiScreen
    from textual.screen import Screen
    from typing import Self

def human_format(num):
    if isinstance(num, str):
        num = int(num)
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

class LOKCharacter(Static):
    """Tintin-helper style character information block"""

    def compose(self) -> ComposeResult:
        yield Static("Character", classes="WidgetTitle", markup=True)
        yield LOKCharacterStatic()

class LOKCharacterStatic(Static):
    """Subwidget to display current Character details"""
    c_name: reactive[str | None] = reactive[str | None](None)
    c_race: reactive[str | None] = reactive[str | None](None)
    c_class: reactive[str | None] = reactive[str | None](None)
    c_level: reactive[int | None] = reactive[int | None](None)
    c_align: reactive[int | None] = reactive[int | None](None)
    c_str: reactive[int | None] = reactive[int | None](None)
    c_int: reactive[int | None] = reactive[int | None](None)
    c_wis: reactive[int | None] = reactive[int | None](None)
    c_dex: reactive[int | None] = reactive[int | None](None)
    c_con: reactive[int | None] = reactive[int | None](None)
    c_luk: reactive[int | None] = reactive[int | None](None)
    c_heros: reactive[int | None] = reactive[int | None](None)
    c_heros_tnl: reactive[int | None] = reactive[int | None](None)
    c_xp: reactive[int | None] = reactive[int | None](None)
    c_xp_tnl: reactive[int | None] = reactive[int | None](None)    
    c_gold: reactive[int | None] = reactive[int | None](None)
    c_gold_bank: reactive[int | None] = reactive[int | None](None)

    def on_mount(self):
        # Register our listener until we have a RegisterableObject to descend from
        self.screen.session.listener(self.update_reactives)
        if self.c_name is None:
            self.display = False

    def render(self) -> RenderResult:
        table = Table(show_header=False,show_edge=False,show_lines=False, box=box.SIMPLE)
        table.padding = 0
        table2 = Table(show_header=False,show_edge=False,show_lines=False, box=box.SIMPLE, expand=True)
        table.add_column(justify="left")
        table.add_row(f"[cyan]{self.c_name}, {self.c_race} {self.c_class} [{self.c_level}]")
        table.add_row(f"[cyan]S:[white]{self.c_str} [cyan]I:[white]{self.c_int} [cyan]W:[white]{self.c_wis} [cyan]D:[white]{self.c_dex} [cyan]C:[white]{self.c_con} [cyan]L:[white]{self.c_luk}\n")

        table2.add_column(justify="right")
        table2.add_column(justify="left")
        table2.add_column(justify="right")
        table2.add_column(justify="left")
        table2.padding = 0
        
        table2.add_row("[cyan]Heros",f"[white]{self.c_heros}","[cyan]TNL",f"[white]{self.c_heros_tnl}")
        table2.add_row("[cyan]XP", f"[white]{human_format(self.c_xp)}", "[cyan]TNL", f"[white]{human_format(self.c_xp_tnl)}")
        table2.add_row("[cyan]Gold", f"[white]{human_format(self.c_gold)}", "[cyan]Bank", f"[white]{human_format(self.c_gold_bank)}")
        table.add_row(table2)

        return table

    @event("msdp_value")
    def update_reactives(self, message: MSDPMessage):
        MY_REACTIVES = {
         "CHARACTER_NAME": "c_name",
          "CLASS": "c_class",
          "LEVEL": "c_level",
          "ALIGNMENT": "c_align",
          "STR": "c_str",
          "INT": "c_int",
          "WIS": "c_wis",
          "DEX": "c_dex",
          "CON": "c_con",
          "LUK": "c_luk",
          "HERO_POINTS": "c_heros",
          "HERO_POINTS_TNL": "c_heros_tnl",
          "EXPERIENCE": "c_xp",
          "EXPERIENCE_TNL": "c_xp_tnl",
          "GOLD": "c_gold",
          "BANK_GOLD": "c_gold_bank",
          "RACE": "c_race",

        }

        if message.type in MY_REACTIVES:
            setattr(self, MY_REACTIVES[message.type], message.value)

        if not self.display and self.c_name is not None:
            self.display = True
