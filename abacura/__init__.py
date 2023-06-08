from __future__ import annotations

from abacura.config import Config

import csv
import io
from serum import inject

from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static, TextLog

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.mud.session import Session    
    

@inject 
class SessionScreen(Screen):
    _config: Config
    _session: Session

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_sidebar", "F2"),
    ]

    CSS_PATH = "abacura.css"
    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str):
        super().__init__()
      
        self.id = f"screen-{name}"
        self.tlid = f"output-{name}"

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        
        with Container(id="app-grid"):
            yield Static("Sidebar\nSessions\nOther data", id="sidebar", name="sidebar")
            with Container(id="mudoutputs"):
                yield TextLog(highlight=False, markup=False, wrap=False, name=self.tlid, classes="mudoutput", id=self.tlid)
            yield InputBar()
        yield AbacuraFooter()
    
    def on_mount(self) -> None:
        self.tl = self.query_one(f"#{self.tlid}", expect_type=TextLog)
        self._session.launch_screen()

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')
        
        try:
            lines = list.__next__()
            for line in lines:
                self._session.player_input(line)
                
        except StopIteration:
            self._session.player_input("")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    def action_pageup(self) -> None:
        self.tl.auto_scroll = False
        self.tl.action_page_up()

    def action_pagedown(self) -> None:
        self.tl.action_page_down()
        if self.tl.scroll_offset.x == 0:
            self.tl.auto_scroll = True

    @property
    def config(self):
        return self._config.config
    


class InputBar(Input):
    class UserCommand(Message):
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def __init__(self,**kwargs):
        super().__init__()
        
    def on_input_submitted(self, message: Input.Submitted) -> None:
        self.post_message(self.UserCommand(self.value))
        self.value = ""

class AbacuraFooter(Footer):
    """Name of current session"""

    session: reactive[str | None] = reactive[str | None]("null")

    def render(self) -> str:
        return f"#{self.session}"    

