import io
import csv

import re
import os

from mud.session import Session

from rich.console import RenderableType
from rich.pretty import Pretty

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import var
from textual.scroll_view import ScrollView
from textual.widgets import Button, Footer, Header, Static, TextLog, Input

from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from typing_extensions import Self

class InputBar(Input):
    class Command(Message):
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def __init__(self,**kwargs):
        super().__init__()
        
    def on_input_submitted(self, message: Input.Submitted) -> None:
        self.post_message(self.Command(self.value))
        self.value = ""

class Abacura(App):
    """A Textual mudclient"""

    session = Session()
    
    AUTO_FOCUS = "InputBar"
    CSS_PATH   = "abacura.css"
    LOGIN = re.compile(r"^Enter your account name.")
    PASSWORD = re.compile(r"^Please enter your account password")

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_sidebar", "F2")        
                ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        with Container(id="app-grid"):
            yield Static("Sidebar\nSessions\nOther data", id="sidebar", name="sidebar")
            yield TextLog(highlight=False, markup=True, name="inputbar", wrap=False, classes="mudoutput")
            yield InputBar()
        #yield Footer()
        
    def handle_mud_data(self, data):
        text_log = self.query_one(TextLog)
        if data == "\r":
            text_log.write("")

        # TODO action handlers
        else:
            if self.LOGIN.match(data):
                self.session.send(os.environ["MUD_USERNAME"])
            elif self.PASSWORD.match(data):
                text_log.write("Entered password")
                self.session.send(os.environ["MUD_PASSWORD"])
            text_log.write(data)

    async def on_input_bar_command(self, command: InputBar.Command) -> None:
        text_log = self.query_one(TextLog)
        
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')

        try:
            lines = list.__next__()
            for line in lines:
            
                cmd = line.lstrip().split()[0]

                # TODO clean this up to support #commands
                if cmd.lower() == "connect":
                    text_log.write(f"Connect to {line.lstrip().split()[1:]}")
                    self.run_worker(self.session.telnet_client(self.handle_mud_data))
                elif cmd.lower() == "dump":
                    self.dump_value(line.lstrip())
                else:
                    if self.session.connected:
                        self.session.send(line + "\n")
                    else:
                        text_log.write("[bold red]# NO SESSION CONNECTED")
        except:
            if self.session.connected: 
                self.session.send("")
            else:
                text_log.write("[bold red]# NO SESSION CONNECTED")
            
    def dump_value(self, value):
        text_log = self.query_one(TextLog)
        words = value.split()
        if len(words) == 1:
            text_log.write(Pretty(self.session.options[69].values))
        else:
            text_log.write(Pretty([words[1], self.session.options[69].values[words[1]]]))

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_pageup(self) -> None:
        text_log = self.query_one(TextLog)
        text_log.auto_scroll = False
        text_log.action_page_up()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
    
        if sidebar._css_styles.display == "block":
            sidebar._css_styles.display = "none"
        else:
            sidebar._css_styles.display = "block"

    def action_pagedown(self) -> None:
        text_log = self.query_one(TextLog)
        text_log.action_page_down()
        if text_log.scroll_offset.x == 0:
            text_log.auto_scroll = True

    def action_quit(self) -> None:
        exit()

if __name__ == "__main__":
    app = Abacura()
    app.run()

