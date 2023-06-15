"""Legends of Kallisti Test Screen"""
from __future__ import annotations

import csv
import io
import os
from typing import TYPE_CHECKING

from serum import inject

from textual import log
from textual.app import ComposeResult
from textual.containers import Container

from textual.screen import Screen
from textual.widgets import Header, TextLog
from textual.widget import Widget

from abacura import InputBar
from abacura.config import Config
from abacura.widgets.inspector import Inspector


from abacura.widgets.sidebar import Sidebar
from abacura.widgets.footer import AbacuraFooter
from abacura.widgets.resizehandle import ResizeHandle

from abacura.plugins import action, Action
from abacura.plugins.events import event

from abacura_kallisti.widgets import KallistiCharacter

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session


class XCL(Widget):
    """Experimental CommsLog"""
    def __init__(self, id: str, name: str = ""):
        super().__init__(id=id, name=name)
        self.tl = TextLog(id="commsTL")
        
    def on_mount(self):
        pass

    def compose(self):
        yield self.tl

    @action("\x1B\[1;35m<Gossip: (.*)> \'(.*)\'")
    def test_gos(self, *args, **kwargs):
        #act = Action(source=self, pattern=pattern, callback=callback_fn, flags=flags, name=name, color=color)
        self.tl.write(f"{args[0]}: {args[1]}")

class BetterSidebar(Sidebar):
    side: str
    def __init__(self, side: str, **kwargs):
        super().__init__(**kwargs)
        self.side = side
        

    def compose(self) -> ComposeResult:
        if self.side == "left":
            yield ResizeHandle(self, "right")
        elif self.side == "right":
            yield ResizeHandle(self, "left")

        yield Container(id=f"{self.side}sidecontainer", classes="SidebarContainer")
            



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
        ("f5", "mount_stuff", "f5")
    ]

    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str):

        super().__init__()
        self.id = f"screen-{name}"
        self.tlid = f"output-{name}"

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        commslog = XCL(id="commslog")
        commslog.display = False

        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        yield BetterSidebar(side="left", id="leftsidebar", name="leftsidebar")
        yield BetterSidebar(side="right",id="rightsidebar", name="rightsidebar")

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

    def on_mount(self) -> None:
        """Screen is mounted, launch it"""
        self.tl = self.query_one(f"#{self.tlid}", expect_type=TextLog)
        self.session.launch_screen()
        cl = self.query_one("#commslog")
        self.session.action_registry.register_object(cl)

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        """Handle user input from InputBar"""
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')

        try:
            lines = list.__next__()
            for line in lines:
                self.session.player_input(line)

        except StopIteration:
            self.session.player_input("")

    def action_mount_stuff(self) -> None:
        lsb = self.query_one("#leftsidecontainer")
        lsb.mount(KallistiCharacter(id="kallisticharacter"))

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

    def action_pageup(self) -> None:
        self.tl.auto_scroll = False
        self.tl.action_page_up()

    def action_pagedown(self) -> None:
        self.tl.action_page_down()
        if self.tl.scroll_offset.x == 0:
            self.tl.auto_scroll = True

class BetterKallistiScreen(KallistiScreen):
    DEFAULT_CLASSES = "BKS"
    pass