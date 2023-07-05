"""Main screen and widgets for abacura"""
from __future__ import annotations

# TODO: screen and widget definitions should go under the hierarchy, not in __init__
import csv
import io
import os
from typing import TYPE_CHECKING, Coroutine, Any

from serum import inject

from textual import log, on
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message

from textual.screen import Screen
from textual.widgets import Header, TextLog

from abacura.config import Config
from abacura.widgets import CommsLog, InputBar

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.footer import AbacuraFooter

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session

@inject
class SessionScreen(Screen):
    """Default Screen for sessions"""
    config: Config
    session: Session

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("shift+end", "scroll_end", ""),
        ("shift+home", "scroll_home", ""),
        ("f2", "toggle_sidebar", "F2"),
        ("f3", "toggle_commslog", "F3")
    ]

    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str):
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
            from abacura.widgets._inspector import Inspector
            inspector = Inspector()
            inspector.display = False
            yield inspector

    def on_mount(self) -> None:
        """Screen is mounted, launch it"""
        self.session.launch_screen()

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        """Handle user input from InputBar"""
        self.session.player_input(command.command, gag=command.password)
        #list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')

        #try:
        #    lines = list.__next__()
        #    for line in lines:
        #        self.session.player_input(line)

        #except StopIteration:
        #    self.session.player_input("")

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

    def action_scroll_home(self) -> None:
        self.tl.auto_scroll = False
        self.tl.action_scroll_home()

    def action_scroll_end(self) -> None:
        self.tl.auto_scroll = True
        self.tl.action_scroll_end()
