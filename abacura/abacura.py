from abacura import AbacuraFooter
from abacura.config import Config
from abacura.mud.session import Session

import click
from serum import Context

from textual.app import App
from textual.screen import Screen


from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from typing_extensions import Self


class Abacura(App):
    """A Textual mudclient"""
    sessions = {}
    session = "null"
    screens: Dict[Session, Screen]

    def __init__(self,config,**kwargs):
        self.config_file = config
        self.config = Config(config=config)
        super().__init__()
 
    AUTO_FOCUS = "InputBar"
    CSS_PATH   = "abacura.css"
    SCREENS = {}

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("f3", "reload_config", "f3")    
                ]
    
    def on_mount(self) -> None:
        self.create_session("null")

    def create_session(self, id: str) -> None:
        with Context(all=self.sessions, _config=self.config, abacura=self):
            self.sessions[id] = Session(id)
        self.session = id

    def set_session(self, id: str) -> None:
        self.session = id
        self.push_screen(id)
        self.query_one(AbacuraFooter).session = id 

    def current_session(self) -> Session:
        return self.sessions[self.session]

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
            
    def action_reload_config(self) -> None:
        tl = self.sessions[self.session].tl
        self.config.reload()
        tl.markup = True
        tl.write(f"[bold red]# CONFIG: Reloaded configuration file")
        tl.markup = False

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