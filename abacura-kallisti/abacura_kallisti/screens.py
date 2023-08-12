"""Legends of Kallisti Test Screen"""
from __future__ import annotations

from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.screen import ModalScreen
from textual.widgets import Header, Button, Placeholder

from abacura.screens import SessionScreen
from abacura.widgets import CommsLog
from abacura.widgets import InputBar
from abacura.widgets.debug import DebugDock
from abacura.widgets.footer import AbacuraFooter
from abacura_kallisti.widgets import LOKLeft, LOKRight, LOKMap

if TYPE_CHECKING:
    from abacura.mud.session import Session


class KallistiScreen(SessionScreen):
    """Default Screen for sessions"""
    BINDINGS = [

        ("f2", "toggle_left_sidebar", "F2"),
        ("f3", "toggle_right_sidebar", "F3"),
        ("f4", "toggle_commslog", "F4"),
        ("f5", "toggle_debug", "F5"),
        ("f6", "toggle_map", "F6")
    ]

    AUTO_FOCUS = "InputBar"
    CSS_PATH = "css/kallisti.css"
    DEFAULT_CLASSES = "BKS"

    def __init__(self, name: str, session: Session):

        super().__init__(name, session)
        self._map_overlay = False
        self.can_focus_children = False

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
                self.tl.can_focus = False
                yield self.tl

            yield InputBar(id="playerinput")

        self.footer = AbacuraFooter(id="footer")
        yield self.footer

        if self.session.abacura.inspector:
            from abacura.widgets._inspector import Inspector
            inspector = Inspector()
            inspector.display = False
            yield inspector
        debugger = DebugDock(id="debugger")
        debugger.display = False
        yield debugger

    def action_toggle_left_sidebar(self) -> None:
        sidebar = self.query_one("#leftsidebar")
        sidebar.display = not sidebar.display

    def action_toggle_right_sidebar(self) -> None:
        sidebar = self.query_one("#rightsidebar")
        sidebar.display = not sidebar.display

    def action_toggle_commslog(self) -> None:
        commslog = self.query_one("#commslog")
        commslog.display = not commslog.display
        self.refresh()

    def action_toggle_debug(self) -> None:
        debugger = self.query_one("#debugger")
        debugger.display = not debugger.display
        self.refresh()

    def action_toggle_map(self) -> None:
        def reset_mapkey():
            self._map_overlay = False

        if not self._map_overlay:
            self._map_overlay = True
            self.app.push_screen(MapScreen(id="LOKMap", session=self.session), reset_mapkey())


class BetterKallistiScreen(KallistiScreen):
    """
    This will eventually be the standard screen for the abacura-kallisti module
    """
    DEFAULT_CLASSES = "BKS"


class MapScreen(ModalScreen[bool]):
    """Screen with a dialog to quit."""

    CSS_PATH = "css/kallisti.css"

    def __init__(self, session: Session, **kwargs):
        super().__init__(id=kwargs["id"], *kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        bigmap = LOKMap(id="bigmap", resizer=False)
        yield Grid(Container(bigmap), id="MapGrid")

    def on_key(self, _event: events.Key) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.dismiss(True)
        else:
            self.dismiss(False)
