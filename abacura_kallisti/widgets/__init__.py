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

class LOKCharacterStatic(Static):
    CharacterName: reactive[str | None] = reactive[str | None](None)
    CharacterClass: reactive[str | None] = reactive[str | None](None)
    CharacterLevel: reactive[int | None] = reactive[int | None](None)

    def on_mount(self):
        """Register event listeners"""
        self.CharacterName = self.screen.session.options[69].values["CHARACTER_NAME"]
        self.CharacterLevel = self.screen.session.options[69].values["LEVEL"]
        self.CharacterClass = self.screen.session.options[69].values["CLASS"]
        self.screen.session.event_manager.listener(self.update_char_name)
        self.screen.session.event_manager.listener(self.update_char_class)

    def render(self) -> str:
        return f"{self.CharacterName} {self.CharacterClass} [{self.CharacterLevel}]"
    
    @event("msdp_value_CHARACTER_NAME")
    def update_char_name(self, message: MSDPMessage):
        self.CharacterName = message.value

    @event("msdp_value_CLASS")
    def update_char_class(self, message: MSDPMessage):
        self.CharacterClass = message.value

