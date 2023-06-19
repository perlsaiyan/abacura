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
        yield Static("Character", classes="WidgetTitle")
        yield LOKCharacterStatic()

class LOKCharacterStatic(Static):
    """Subwidget to display current Character details"""
    character_name: reactive[str | None] = reactive[str | None](None)
    character_class: reactive[str | None] = reactive[str | None](None)
    character_level: reactive[int | None] = reactive[int | None](None)
    mud_uptime: reactive[int | None] = reactive[int | None](None)

    # TODO this could be cleaner, and potentially one-shot msdp reactives
    def on_mount(self):
        # Register our listener until we have a RegisterableObject to descend from
        self.screen.session.listener(self.update_reactives)

    def render(self) -> str:
        return f"{self.character_name} {self.character_class} " + \
            f"[{self.character_level}]\n{self.mud_uptime}\n" + \
            "\nStr: ONE MILLION int: wis: blah\n" + \
            f"[green]Gold: [white] [green]Bank: [white]All\n" + \
            "[green]Estimated Meta Sessions: [white]69"

    @event("msdp_value")
    def update_reactives(self, message: MSDPMessage):
        MY_REACTIVES = {
         "CHARACTER_NAME": "character_name",
          "CLASS": "character_class",
          "LEVEL": "character_level",
          "UPTIME": "mud_uptime"
        }

        if message.type in MY_REACTIVES:
            setattr(self, MY_REACTIVES[message.type], message.value)
