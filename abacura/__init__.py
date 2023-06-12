"""Main screen and widgets for abacura"""
from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Coroutine, Any

from rich.align import Align
from rich.text import Text
from serum import inject

from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Footer, Header, Input, TextLog

from abacura.config import Config
from abacura.inspector import Inspector
from abacura.widgets.sidebar import Sidebar
from abacura.widgets.commslog import CommsLog

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session    

@inject
class SessionScreen(Screen):
    """Default Screen for sessions"""
    config: Config
    _session: Session

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_sidebar", "F2"),
        ("f3", "toggle_commslog", "F3")
    ]

    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str):
        self.CSS_PATH = self.config.get_specific_option(self._session.name, "css_path") or "abacura.css"
        super().__init__()

        self.id = f"screen-{name}"
        self.tlid = f"output-{name}"

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        commslog = CommsLog(id="commslog", name="commslog")
        commslog.display = False
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        yield commslog

        with Container(id="app-grid"):
            yield Sidebar(id="sidebar", name="sidebar")
            with Container(id="mudoutputs"):
                # TODO: wrap should be a config file field option
                yield TextLog(highlight=False, markup=False, wrap=True,
                              name=self.tlid, classes="mudoutput", id=self.tlid)
            yield InputBar()
        yield AbacuraFooter()
        inspector = Inspector()
        inspector.display = False
        yield inspector

    def on_mount(self) -> None:
        """Screen is mounted, launch it"""
        self.tl = self.query_one(f"#{self.tlid}", expect_type=TextLog)
        self._session.launch_screen()

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        """Handle user input from InputBar"""
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')

        try:
            lines = list.__next__()
            for line in lines:
                self._session.player_input(line)

        except StopIteration:
            self._session.player_input("")

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

    def __init__(self):
        super().__init__()
        self.history = []
        self.history_ptr = None

    def on_mount(self):
        self.suggester = AbacuraSuggester(self.screen._session)

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

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """Bubble-up player input and blank the bar"""

        self.suggester.add_entry(self.value)
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

    async def get_suggestion(self, value: str) -> Coroutine[Any, Any, str | None]:
        if value.startswith("@"):
            value = value[1:]
            for handler in self.session.plugin_manager.plugin_handlers:
                for com in handler.command_functions:
                    if com.name.startswith(value):
                        return f"@{com.name}"
        else:
            log.info(f"Completing with {self.history}")
            try:
                for cmds in self.history:
                    if cmds.startswith(value):
                        return cmds
            # empty list
            except TypeError:
                return None

        return None

class AbacuraFooter(Footer):
    """Bottom of screen bar with current session name"""

    session: reactive[str | None] = reactive[str | None]("null")

    def render(self) -> str:
        return f"#{self.session}"
