"""Main Textual App and Entrypoint"""
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Dict, Optional
from collections import OrderedDict

import click
from serum import Context, inject
from textual.app import App
from textual.binding import Binding
from textual.screen import Screen

from abacura import AbacuraFooter
from abacura.config import Config
from abacura.mud.session import Session
from abacura import Inspector
from abacura.utils import pycharm

if TYPE_CHECKING:
    from typing_extensions import Self

@inject
class Abacura(App):
    """A Textual mudclient"""
    screens: Dict[Session, Screen]
    config: Config

    AUTO_FOCUS = "InputBar"
    CSS_PATH = ["abacura.css"]
    SCREENS = {}
    START_SESSION: Optional[str] = None
    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("f3", "reload_config", "f3"),
        Binding("f12", "toggle_inspector", ("Toggle Inspector")),
                ]

    def __init__(self):
        super().__init__()
        self.sessions: OrderedDict[str, Session] = OrderedDict()
        self.session = "null"

    def on_mount(self) -> None:
        """When app is mounted, create first session"""
        self.create_session("null")
        if self.START_SESSION:
            self.sessions["null"].connect(self.START_SESSION)


    def create_session(self, name: str) -> None:
        """Create a session"""
        with Context(config=self.config, abacura=self):
            self.sessions[name] = Session(name)
        self.session = name

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

    def action_toggle_inspector(self) -> None:
        inspector = self.query_one(Inspector)
        inspector.display = not inspector.display
        if not inspector.display:
            inspector.picking = False

@click.command()
@click.option("-c","--config", 'config')
@click.option("-d", "--debug", "debug", type=str)
@click.option("-s", "--start", "start", type=str)
@click.pass_context
def main(ctx, config, debug, start):
    if debug:
        host, port = debug.split(":")
        pycharm.PycharmDebugger().connect(host, int(port))

    """Entry point for client"""
    _config = Config(config=config)

    mods_to_load = _config.get_specific_option("global","module_paths")
    if mods_to_load:
        if isinstance(mods_to_load, list):
            for path in mods_to_load:
                sys.path.append(str(Path(path).expanduser()))
        else:
            sys.path.append(str(Path(mods_to_load).expanduser()))

    usercss = _config.get_specific_option("global", "css_path")

    if usercss:
        if isinstance(usercss, str):
            usercss = [usercss]
        usercss.extend(Abacura.CSS_PATH)
        Abacura.CSS_PATH = usercss

    with Context(config=_config):
        app = Abacura()

    Abacura.START_SESSION = start

    app.run()
