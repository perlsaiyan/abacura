from abacura import AbacuraFooter
from abacura.config import Config
from abacura.mud.session import Session
from abacura import Inspector

import click
from tomlkit import TOMLDocument
from pathlib import Path
from serum import Context, inject
import sys

from textual.app import App
from textual.binding import Binding
from textual.screen import Screen


from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from typing_extensions import Self

@inject
class Abacura(App):
    """A Textual mudclient"""
    sessions = {}
    session = "null"
    screens: Dict[Session, Screen]
    _config: Config

    AUTO_FOCUS = "InputBar"
    CSS_PATH: str = "abacura.css"
    SCREENS = {}

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("f3", "reload_config", "f3"),
        Binding("f12", "toggle_inspector", ("Toggle Inspector")),
                ]

    def __init__(self,**kwargs):
        super().__init__()
    
    def on_mount(self) -> None:
        self.create_session("null")

    def create_session(self, id: str) -> None:
        with Context(all=self.sessions, _config=self._config, abacura=self):
            self.sessions[id] = Session(id)
        self.session = id

    def set_session(self, id: str) -> None:
        self.session = id
        self.push_screen(id)
        self.query_one(AbacuraFooter).session = id 

    def action_reload_config(self) -> None:
        tl = self.sessions[self.session].tl
        self.config.reload()
        tl.markup = True
        tl.write(f"[bold red]# CONFIG: Reloaded configuration file")
        tl.markup = False

    def action_quit(self) -> None:
        exit()

    def action_toggle_inspector(self) -> None:
        inspector = self.query_one(Inspector)
        inspector.display = not inspector.display
        if not inspector.display:
            inspector.picking = False

    @property
    def config(self) -> TOMLDocument:
        return self._config.config


@click.command()
@click.option("-c","--config", 'config')
@click.pass_context
def main(ctx,config):
    _config = Config(config=config)
    c = _config.config

    if "global" in c and "module_paths" in c["global"]:
            if isinstance(c["global"]["module_paths"], list):
                for p in c["global"]["module_paths"]:
                    sys.path.append(str(Path(p).expanduser()))
            else:
                sys.path.append(str(Path(c["global"]["module_paths"]).expanduser()))

    if "global" in c and "css_path" in c["global"]:
        css_path = c["global"]["css_path"]
    else:
        css_path = "abacura.css"

    with Context(_config=_config, CSS_PATH=css_path):
        app = Abacura()
    app.run()

if __name__ == "__main__":
    main()
