from textual.app import ComposeResult
from textual.containers import Container

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.resizehandle import ResizeHandle

from abacura_kallisti.widgets import KallistiCharacter

class LOKLeft(Sidebar):
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "right")
        with Container(id="leftsidecontainer", classes="SidebarContainer"):
            yield KallistiCharacter(id="kallisticharacter")

class LOKRight(Sidebar):
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "left")
        yield Container(id="rightsidecontainer", classes="SidebarContainer")
    
