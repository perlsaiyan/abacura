from typing import TYPE_CHECKING
from textual import log
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static, TextLog, ProgressBar

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

if TYPE_CHECKING:
    from abacura import Session
    from textual.screen import Screen




class KallistiCharacter(Static):

    def compose(self) -> ComposeResult:
        yield Static("Character", classes="WidgetTitle")
        yield LOKCharacterStatic()

        yield Static("Affects", classes="WidgetTitle")

        yield Static("Mount", classes="WidgetTitle")

        yield Static("RemortInfo", classes="WidgetTitle")

class LOKCharacterStatic(Static):
    """Subwidget to display current Character details"""
    character_name: reactive[str | None] = reactive[str | None](None)
    character_class: reactive[str | None] = reactive[str | None](None)
    character_level: reactive[int | None] = reactive[int | None](None)

    def on_mount(self):
        """Register event listeners"""
        for hook in [("character_name", "CHARACTER_NAME", self.update_char_name),
                     ("character_class", "CLASS", self.update_char_class),
                     ("character_level", "LEVEL", self.update_char_level)]:
            self.msdp_seed_and_subscribe(*hook)


    def render(self) -> str:
        return f"{self.character_name} {self.character_class} [{self.character_level}]"

    @event("msdp_value_CHARACTER_NAME")
    def update_char_name(self, message: MSDPMessage):
        self.character_name = message.value

    @event("msdp_value_CLASS")
    def update_char_class(self, message: MSDPMessage):
        self.character_class = message.value

    @event("msdp_value_LEVEL")
    def update_char_level(self, message: MSDPMessage):
        self.character_level = message.value

    def msdp_seed_and_subscribe(self, local_val: str, msdp_val: str, func: callable):
        """Grab an initial value and subscribe to an @event"""
        log(f"Test subscribe to {msdp_val}")
        if msdp_val in self.screen.session.options[69].values:
            setattr(self, local_val, self.screen.session.options[69].values[msdp_val])
        else:
            local_val = None
        self.screen.session.event_manager.listener(func)
