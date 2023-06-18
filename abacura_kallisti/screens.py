"""Legends of Kallisti Test Screen"""
from __future__ import annotations

import csv
import io
import os
from typing import TYPE_CHECKING

from serum import inject

from textual import log, events
from textual.app import ComposeResult
from textual.containers import Container, Grid

from textual.screen import Screen, ModalScreen
from textual.widgets import Header, TextLog, Static, Button

from abacura import InputBar
from abacura.config import Config
from abacura.widgets import Inspector, CommsLog
from abacura.widgets.footer import AbacuraFooter
from abacura.widgets.debug import DebugDock

from abacura_kallisti.widgets import LOKLeft, LOKRight


if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session
    from abacura.plugins.director import Director
    
@inject
class KallistiScreen(Screen):
    """Default Screen for sessions"""
    config: Config
    session: Session

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_left_sidebar", "F2"),
        ("f3", "toggle_right_sidebar", "F3"),
        ("f4", "toggle_commslog", "F4"),
        ("f5", "toggle_debug", "F5"),
        ("f6", "toggle_map", "F6")
    ]

    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str):

        super().__init__()
        self.id = f"screen-{name}"
        self.tlid = f"output-{name}"
        self._map_overlay = False

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        commslog = CommsLog(id="commslog")
        commslog.display = False

        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        yield LOKLeft(id="leftsidebar", name="leftsidebar")
        yield LOKRight(id="rightsidebar", name="rightsidebar")

        with Container(id="app-grid"):
            yield commslog
            
            with Container(id="mudoutputs"):
                # TODO: wrap should be a config file field option
                yield TextLog(highlight=False, markup=False, wrap=True,
                              name=self.tlid, classes="mudoutput", id=self.tlid)
            yield InputBar()
        yield AbacuraFooter()
        inspector = Inspector()
        inspector.display = False
        yield inspector
        debugger = DebugDock(id="debugger")
        debugger.display = False
        yield debugger

    def on_mount(self) -> None:
        """Screen is mounted, launch it"""
        self.tl = self.query_one(f"#{self.tlid}", expect_type=TextLog)
        self.session.tl = self.tl
        self.session.launch_screen()
        cl = self.query_one("#commslog")
        self.session.director.register_object(cl)

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

    def action_toggle_left_sidebar(self) -> None:
        sidebar = self.query_one("#leftsidebar")
        sidebar.display = not sidebar.display

    def action_toggle_right_sidebar(self) -> None:
        BetterKallistiScreen.CSS_PATH = os.getenv("HOME") + "/a.css",
        sidebar = self.query_one("#rightsidebar")
        sidebar.display = not sidebar.display

    def action_toggle_commslog(self) -> None:
        commslog = self.query_one("#commslog")
        commslog.display = not commslog.display

    def action_toggle_debug(self) -> None:
        debugger = self.query_one("#debugger")
        debugger.display = not debugger.display

    def action_pageup(self) -> None:
        self.tl.auto_scroll = False
        self.tl.action_page_up()

    def action_pagedown(self) -> None:
        self.tl.action_page_down()
        if self.tl.scroll_offset.x == 0:
            self.tl.auto_scroll = True
    
    def action_toggle_map(self) -> None:
        def reset_mapkey():
            self._map_overlay = False

        if not self._map_overlay:
            self._map_overlay = True
            if self._map_overlay:
                self.app.push_screen(MapScreen(id="LOKMap"), reset_mapkey())

class BetterKallistiScreen(KallistiScreen):
    """
    Subclassing the screen to test using class inheritence to get per-screen styles

    After the next release of Textual this will not be necessary as screens can have
    their own stylesheet and CSS_PATH
    """
    DEFAULT_CLASSES = "BKS"
    pass

class MapScreen(ModalScreen[bool]):  
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        log(f"{self.css_identifier_styled} popover")
        yield Grid(
                Static("Map Overlay Screen", id="label"),
                id="MapGrid"
        )

    def on_key(self, event: events.Key) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.dismiss(True)
        else:
            self.dismiss(False)
