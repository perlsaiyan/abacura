import random

from textual import log
from textual.app import ComposeResult
from textual.events import Resize
from textual.containers import Container, Center, Middle
from textual.widget import Widget
from textual.widgets import Static

from abacura.widgets.resizehandle import ResizeHandle

class LOKMap(Container):

    def __init__(self, resizer: bool=True, id: str=""):
        super().__init__()
        self.id=id
        self.resizer: bool = resizer
        self.map = Static(id="minimap", classes="lokmap", expand=True)
        

    def compose(self) -> ComposeResult:
        with Middle():
            yield self.map
        if self.resizer:
            yield ResizeHandle(self, "bottom")

    def generate_map(self) -> None:
        log("regenerate a MAP")
        H = self.content_size.height - 1
        W = self.content_size.width
        cH = int(H/3)
        cW = int(W/5)
        fW = cW*5
        self.map.styles.width = fW
        Matrix = [[0 for x in range(cW)] for y in range(cH)]
        

        cenH = int(cH/2)
        cenW = int(cW/2)
        buf = f"width {self.map.container_size.width} or {W}\n"
        buf += f"height {self.map.container_size.height} or {H}\n"
        buf += f"viewport {self.content_size}\n"
        buf += f"rooms: {cW}x{cH}\n"
        buf += f"{cenW} {cenH}"

        
        self.map.update(buf)
    
    def on_resize(self, event: Resize):
        self.generate_map()
