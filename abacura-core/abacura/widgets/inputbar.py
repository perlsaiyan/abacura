"""Main screen and widgets for abacura"""
from __future__ import annotations

# TODO: screen and widget definitions should go under the hierarchy, not in __init__
import csv
import io
from typing import TYPE_CHECKING, Coroutine, Any

from textual import log, on
from textual.binding import Binding
from textual.message import Message
from textual.suggester import Suggester
from textual.widgets import Input

from abacura.plugins.events import event, AbacuraMessage

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session

class InputBar(Input):
    BINDINGS = [
        ("up", "history_scrollback", None),
        ("down", "history_scrollforward", None),
        ("tab", "cursor_right", None),
        Binding("ctrl+c", "clear", None),
    ]

    """player input line"""
    class UserCommand(Message):
        """Message object to bubble up inputs with"""
        def __init__(self, command: str, password: bool = False) -> None:
            self.command = command
            self.password: bool = password
            super().__init__()

    def __init__(self, id: str=""):
        super().__init__(id=id)
        self.history = []
        self.history_ptr = None
        self.styles.padding = (0,0)

    def on_mount(self):
        self.suggester = AbacuraSuggester(self.screen.session)
        self.screen.session.add_listener(self.password_mode)

    @event("core.password_mode")
    def password_mode(self, msg: AbacuraMessage):
        if msg.value == "on":
            self.password = True
            return
        self.password = False

    def action_history_scrollback(self) -> None:
        if self.history_ptr is None:
            self.history_ptr = len(self.history)

        self.history_ptr -= 1

        # reached the top
        if self.history_ptr == -1:
            self.history_ptr = 0
            return

        self.value = self.history[self.history_ptr]

    def action_history_scrollforward(self) -> None:
        if self.history_ptr is None:
            return

        self.history_ptr += 1

        if self.history_ptr >= len(self.history):
            self.history_ptr = None
            self.value = ""
            return

        self.value = self.history[self.history_ptr]

    @on(Input.Changed)
    async def stop_input_change_propagation(self, message) -> None:
        message.stop()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """Bubble-up player input and blank the bar"""

        if not self.password and len(self.value):
            self.suggester.add_entry(self.value)
            self.history.append(self.value)

        self.history_ptr = None
        self.post_message(self.UserCommand(message.value, self.password))
        self.value = ""
    
    def action_clear(self) -> None:
        self.value=""

class AbacuraSuggester(Suggester):
    def __init__(self, session):
        super().__init__(use_cache=False)
        self.session = session
        self.history = []
        self.command_char = self.session.config.get_specific_option(self.session.name, "command_char","#")

    def add_entry(self, value) -> None:
        self.history.insert(0,value)

    async def get_suggestion(self, value: str) -> Coroutine[Any, Any, str] | None:
        if value.startswith(self.command_char):
            value = value[1:]
            for command in self.session.director.command_manager.commands:
                if command.name.startswith(value):
                    return f"{self.command_char}{command.name}"
        else:
            try:
                for cmds in self.history:
                    if cmds.startswith(value):
                        return cmds
            # empty list
            except TypeError:
                return None

        return None
