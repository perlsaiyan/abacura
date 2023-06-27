from __future__ import annotations

from typing import TYPE_CHECKING

from textual import log
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static

from rich.pretty import Pretty

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

if TYPE_CHECKING:
    from abacura import Session
    from abacura_kallisti.screens import BetterKallistiScreen
    from textual.screen import Screen
    from typing import Self

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

    def render(self) -> str:
        buf = f"[cyan]{self.c_name}, {self.c_race} {self.c_class} [{self.c_level}]\n"
        buf += f"\n[cyan]S:[white]{self.c_str} [cyan]I:[white]{self.c_int} [cyan]W:[white]{self.c_wis} [cyan]D:[white]{self.c_dex} [cyan]C:[white]{self.c_con} [cyan]L:[white]{self.c_luk}\n"
        buf += f"\n[cyan]Heros: [white]{self.c_heros} [cyan]TNL: [white]{self.c_heros_tnl}"
        buf += f"\n[cyan]XP: [white]{self.c_xp} [cyan]XPTNL: [white]{self.c_xp_tnl}"
        buf += f"\n[cyan] Gold: [white]{self.c_gold} [cyan]Bank: [white]{self.c_gold_bank}"
        
        return buf

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
