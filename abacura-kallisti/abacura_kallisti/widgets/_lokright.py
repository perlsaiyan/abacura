"""Legends of Kallisti Right Side Panel Dock"""
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.resizehandle import ResizeHandle

from abacura_kallisti.widgets import LOKMap, LOKZone, LOKGroup, LOKCombat

class LOKRight(Sidebar):
    """Right hand dock, intended for user widgets"""
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "left")
        with Container(id="rightsidecontainer", classes="SidebarContainer"):
            yield LOKMap(id="lokmap")
            yield LOKZone(id="lokzone")
            yield LOKGroup(id="lokgroup")
            yield LOKCombat(id="lokcombat")
            yield Static("Action Queues", classes="WidgetTitle")
            yield Static("[green]Priority: [white]0 [green]Heal: [white]0  [green]Any: [white]0\n" + \
                         "[green]  Combat: [white]0 [green] NCO: [white]0 [green]Move: [white]0")