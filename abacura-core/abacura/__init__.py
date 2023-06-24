"""Main screen and widgets for abacura"""
from __future__ import annotations

# TODO: screen and widget definitions should go under the hierarchy, not in __init__
import csv
import io
from typing import TYPE_CHECKING, Coroutine, Any

from serum import inject

from textual import log, on
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message

from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Header, Input, TextLog

from abacura.config import Config
from abacura.widgets import CommsLog

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.footer import AbacuraFooter

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session


version= "0.0.9"

@inject
class SessionScreen(Screen):
    """Default Screen for sessions"""
    config: Config
    session: Session

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_sidebar", "F2"),
        ("f3", "toggle_commslog", "F3")
    ]

    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str):
        # TODO The 0.28.0 release of textual let us assign CSS_PATH at the screen level
        self.CSS_PATH = self.config.get_specific_option(self.session.name, "css_path") or "css/abacura.css"
        super().__init__()

        self.id = f"screen-{name}"
        self.tlid = f"output-{name}"
        # TODO: wrap should be a config file field option
        self.tl = TextLog(highlight=False, markup=False, wrap=True,
                              name=self.tlid, classes="mudoutput", id=self.tlid)

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        commslog = CommsLog(id="commslog", name="commslog")
        commslog.display = False
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        yield commslog

        with Container(id="app-grid"):
            yield Sidebar(id="sidebar", name="sidebar")
            with Container(id="mudoutputs"):
                yield self.tl
            yield InputBar(id="playerinput")
        yield AbacuraFooter()
        if self.session.abacura.inspector:
            from abacura import Inspector
            inspector = Inspector()
            inspector.display = False
            yield inspector

    def on_mount(self) -> None:
        """Screen is mounted, launch it"""
        self.session.launch_screen()

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        """Handle user input from InputBar"""
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')

        try:
            lines = list.__next__()
            for line in lines:
                self.session.player_input(line)

        except StopIteration:
            self.session.player_input("")

    def action_toggle_dark(self) -> None:
        """Dark mode"""
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    def action_toggle_commslog(self) -> None:
        commslog = self.query_one("#commslog")
        commslog.display = not commslog.display

    def action_pageup(self) -> None:
        self.tl.auto_scroll = False
        self.tl.action_page_up()

    def action_pagedown(self) -> None:
        self.tl.action_page_down()
        if self.tl.scroll_offset.x == 0:
            self.tl.auto_scroll = True

class InputBar(Input):
    BINDINGS = [
        ("up", "history_scrollback", None),
        ("down", "history_scrollforward", None),
        ("tab", "cursor_right", None),
    ]

    """player input line"""
    class UserCommand(Message):
        """Message object to bubble up inputs with"""
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def __init__(self, id: str=""):
        super().__init__(id=id)
        self.history = []
        self.history_ptr = None

    def on_mount(self):
        self.suggester = AbacuraSuggester(self.screen.session)

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

        if not self.password:
            self.suggester.add_entry(self.value)
            self.history.append(self.value)

        self.history_ptr = None
        self.post_message(self.UserCommand(self.value))
        self.value = ""

class AbacuraSuggester(Suggester):
    def __init__(self, session):
        super().__init__(use_cache=False)
        self.session = session
        self.history = []

    def add_entry(self, value) -> None:
        self.history.insert(0,value)

    async def get_suggestion(self, value: str) -> Coroutine[Any, Any, str] | None:
        if value.startswith("@"):
            value = value[1:]
            for command in self.session.director.command_manager.commands:
                if command.name.startswith(value):
                    return f"@{command.name}"
        else:
            try:
                for cmds in self.history:
                    if cmds.startswith(value):
                        return cmds
            # empty list
            except TypeError:
                return None

        return None
