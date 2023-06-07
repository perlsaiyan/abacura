from abacura import InputBar, AbacuraFooter
from abacura.config import Config
from abacura.mud.session import Session

import io

import csv
from serum import Context

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Static, TextLog



import click


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class Abacura(App):
    """A Textual mudclient"""
    sessions = {}
    session = "null"

    def __init__(self,config,**kwargs):
        self.config_file = config
        self.config = Config(config=config)
        super().__init__()
 
    AUTO_FOCUS = "InputBar"
    CSS_PATH   = "abacura.css"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("f2", "toggle_sidebar", "F2"),
        ("f3", "reload_config", "f3")    
                ]
    
    def on_mount(self) -> None:
        self.create_session("null")

    def create_session(self, id: str) -> None:
        with Context(all=self.sessions, _config=self.config, abacura=self):
            self.sessions[id] = Session(id)
        
        
    def add_session(self, ses: Session) -> TextLog:
        outputs = self.query_one("#mudoutputs")
        TL = TextLog(highlight=False, markup=True, wrap=False, name=ses.name, classes="mudoutput", id=f"mud-{ses.name}")
        TL.write(f"[bold red]#SESSION {ses.name}")
        
        outputs.mount(TL)
        self.set_session(ses.name)
        return TL

    def set_session(self, id: str) -> None:
        old = self.mudoutput(self.session)
        self.session = id
        new = self.mudoutput(id)
        old.display = False
        new.display = True

        self.query_one(AbacuraFooter).session = new.name 


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
                yield Static(name="MOTD", id="motd")
                #yield TextLog(highlight=False, markup=True, wrap=False, name="null", classes="mudoutput", id="zero")
                #yield TextLog(highlight=False, markup=True, wrap=False, name="pif", classes="mudoutput", id="mud-pif")
            yield InputBar()
        yield AbacuraFooter()
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
            if markup:
                text_log.markup = True
            if highlight:
                text_log.highlight = True

            text_log.write(data)

            text_log.markup = False
            text_log.highlight = False

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        
        ses = self.current_session()
        list = csv.reader(io.StringIO(command.command), delimiter=';', escapechar='\\')
        
        try:
            lines = list.__next__()
            for line in lines:
                ses.player_input(line)
                
        except StopIteration:
            ses.player_input("")

            
    def action_reload_config(self) -> None:
        text_log = self.mudoutput(self.session)
        self.config.reload()
        text_log.markup = True
        text_log.write(f"[bold red]# CONFIG: Reloaded configuration file")
        text_log.markup = False

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    def action_pageup(self) -> None:
        text_log = self.mudoutput(self.session)
        text_log.auto_scroll = False
        text_log.action_page_up()

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

