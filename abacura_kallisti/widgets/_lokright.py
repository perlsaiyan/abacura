"""Legends of Kallisti Right Side Panel Dock"""
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.resizehandle import ResizeHandle

from abacura_kallisti.widgets import LOKCharacter

           
class LOKRight(Sidebar):
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "left")
        with Container(id="rightsidecontainer", classes="SidebarContainer"):
            yield Static("Pending Sixel Support :)", classes="Map")
            yield Static("Zone", classes="WidgetTitle")
            yield Static("[bright blue]Ruins of DongDong\n[green]Level: [white]75-100")
            yield Static("Action Queues", classes="WidgetTitle")
            yield Static("[green]Priority: [white]0 [green]Heal: [white]0  [green]Any: [white]0\n" + \
                         "[green]  Combat: [white]0 [green] NCO: [white]0 [green]Move: [white]0")