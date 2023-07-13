"""Legends of Kallisti Test Screen"""
from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

from serum import inject

from textual import log, events
from textual.app import ComposeResult
from textual.containers import Container, Grid

from textual.screen import Screen, ModalScreen
from textual.widgets import Header, TextLog, Button

from abacura_kallisti.widgets import LOKLeft, LOKRight, LOKMap

from abacura.config import Config
from abacura.widgets import InputBar
from abacura.screens import SessionScreen
from abacura.widgets import CommsLog
from abacura.widgets.footer import AbacuraFooter
from abacura.widgets.debug import DebugDock





if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session
    from abacura_kallisti.atlas.world import World


@inject
class KallistiScreen(SessionScreen):
    """Default Screen for sessions"""
    world: World

    BINDINGS = [

        ("f2", "toggle_left_sidebar", "F2"),
        ("f3", "toggle_right_sidebar", "F3"),
        ("f4", "toggle_commslog", "F4"),
        ("f5", "toggle_debug", "F5"),
        ("f6", "toggle_map", "F6")
    ]

    AUTO_FOCUS = "InputBar"
    CSS_PATH="css/kallisti.css"
    DEFAULT_CLASSES = "BKS"

    def __init__(self, name: str):

        super().__init__(name)
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
                #yield TextLog(highlight=False, markup=False, wrap=True,
                #              name=self.tlid, classes="mudoutput", id=self.tlid)
                self.tl.can_focus = False
                yield self.tl
            yield InputBar(id="playerinput")
        yield AbacuraFooter()
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

    def action_toggle_debug(self) -> None:
        debugger = self.query_one("#debugger")
        debugger.display = not debugger.display

    def action_toggle_map(self) -> None:
        def reset_mapkey():
            self._map_overlay = False

        if not self._map_overlay:
            self._map_overlay = True
            self.app.push_screen(MapScreen(id="LOKMap", session=self.session, world=self.world), reset_mapkey())

class BetterKallistiScreen(KallistiScreen):
    """
    This will eventually be the standard screen for the abacura-kallisti module
    """
    DEFAULT_CLASSES = "BKS"

class MapScreen(ModalScreen[bool]):  
    """Screen with a dialog to quit."""

    CSS_PATH="css/kallisti.css"

    def __init__(self, session: Session, world: World, **kwargs):
        super().__init__(id=kwargs["id"],*kwargs)
        self.session = session
        self.world = world

    def compose(self) -> ComposeResult:
        
        bigmap = LOKMap(id="bigmap", resizer=False)
        bigmap.START_ROOM = str(self.session.core_msdp.values.get("ROOM_VNUM", ""))
        yield Grid(
                bigmap, 
                id="MapGrid"
        )

    def on_key(self, event: events.Key) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.dismiss(True)
        else:
            self.dismiss(False)
