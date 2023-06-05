import io
import csv

import re
import os

from abacura.config import Config
from abacura.mud.context import Context
from abacura.mud.session import Session

from abacura.plugins.plugin import PluginManager

import click

from rich.console import RenderableType

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import var, reactive
from textual.scroll_view import ScrollView
from textual.widget import Widget
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

class SessionName(Footer):
    """Name of current session"""

    session = reactive("null")

    def render(self) -> str:
        return f"#{self.session}"
    
class Abacura(App):
    """A Textual mudclient"""
    def __init__(self,config,**kwargs):
        self.sessions = {}
        self.sessions["null"] = Session("null")
        self.session = "null"
        self.config = Config(config=config)

        super().__init__()
        self.plugin_manager = PluginManager(self, "Global", None)
        self.plugin_manager.load_plugins()        
    
    AUTO_FOCUS = "InputBar"
    CSS_PATH   = "abacura.css"
    LOGIN = re.compile(r"^Enter your account name.")
    PASSWORD = re.compile(r"^Please enter your account password")

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_sidebar", "F2"),     
        ("f3", "exit_with_info", "f3"),
        ("f4", "swap_session", "swap")
                ]

    def on_mount(self) -> None:
        pass

    def action_exit_with_info(self) -> None:
        op = self.mudoutput(self.session)
        ses = self.current_session()
        exit(f"On session {op} {op._css_styles.__dict__}")
    
    def action_swap_session(self) -> None:
        if self.session == "null":
            self.set_session("pif")
        else:
            self.set_session("null")

    def add_session(self, id) -> None:
        outputs = self.query_one("#mudoutputs")
        TL = TextLog(highlight=False, markup=True, wrap=False, name=id, classes="mudoutput", id=f"mud-{id}")
        #TL.disabled = False
        #TL._css_styles.display = "block" 
        TL.write(f"[bold red]#SESSION {id}")
        
        outputs.mount(TL)
        
        newsession = Session(id)
        self.sessions[id] = newsession
        outputs._update_styles()

    def set_session(self, id: str) -> None:
        old = self.mudoutput(self.session)
        self.session = id
        new = self.mudoutput(id)
        old._css_styles.display = "none"
        new._css_styles.display = "block"

        self.query_one(SessionName).session = new.name


    def mudoutput(self, id: str) -> TextLog:
        return self.query_one(f"#mud-{id}", expect_type=TextLog)
    
    def current_session(self) -> Session:
        return self.sessions[self.session]
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        
        with Container(id="app-grid"):
            yield Static("Sidebar\nSessions\nOther data", id="sidebar", name="sidebar")
            with Container(id="mudoutputs"):
                yield TextLog(highlight=False, markup=True, wrap=False, name="null", classes="mudoutput", id="mud-null")
                #yield TextLog(highlight=False, markup=True, wrap=False, name="pif", classes="mudoutput", id="mud-pif")
            yield InputBar()
        yield SessionName()
        #yield Footer()
        
    def handle_mud_data(self, id, data, markup: bool=False, highlight: bool=False):
        if id == None:
            id = self.current_session().name

        text_log = self.mudoutput(id)
        ses = self.sessions[id]
        
        if data == "\r":
            text_log.write("")

        # TODO action handlers
        else:
            if self.LOGIN.match(data):
                ses.send(os.environ["MUD_USERNAME"])
            elif self.PASSWORD.match(data):
                text_log.write("Entered password")
                ses.send(os.environ["MUD_PASSWORD"])
            
            if markup:
                text_log.markup = True
            if highlight:
                text_log.highlight = True

            text_log.write(data)

            text_log.markup = False
            text_log.highlight = False

    async def on_input_bar_command(self, command: InputBar.Command) -> None:
        text_log = self.mudoutput(self.session)
        ses = self.current_session()
        
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')

        try:
            lines = list.__next__()
            for line in lines:

                cmd = line.lstrip().split()[0]

                # This is a command for the global manager
                if cmd.startswith("@") and self.plugin_manager.handle_command(line):
                        continue

                if ses.connected:
                    ses.send(line + "\n")
                    continue
                
                text_log.markup = True
                text_log.write("[bold red]# NO SESSION CONNECTED")
                text_log.markup = False

        except Exception as e:
            if ses.connected: 
                ses.send("")
            else:
                text_log.markup = True
                text_log.write(f"[bold red]# NO SESSION CONNECTED")
                text_log.markup = False
            
    def dump_value(self, value):
        text_log = self.mudoutput(self.session)
        text_log.markup = True
        ses = self.current_session()

        words = value.split()
        if len(words) == 1:
            text_log.write(Pretty(ses.options[69].values), markup=True, highlight=True)
        else:
            text_log.write(Pretty([words[1], ses.options[69].values[words[1]]]), markup=True, highlight=True)
        
        text_log.markup = False

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_pageup(self) -> None:
        text_log = self.mudoutput(self.session)
        text_log.auto_scroll = False
        text_log.action_page_up()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
    
        if sidebar._css_styles.display == "block":
            sidebar._css_styles.display = "none"
        else:
            sidebar._css_styles.display = "block"

    def action_pagedown(self) -> None:
        text_log = self.mudoutput(self.session)
        text_log.action_page_down()
        if text_log.scroll_offset.x == 0:
            text_log.auto_scroll = True

    def action_quit(self) -> None:
        exit()

@click.command()
@click.option("-c","--config", 'config')
@click.pass_context
def main(ctx,config):
    app = Abacura(config)
    app.run()

if __name__ == "__main__":
    main()
