from textual.widget import Widget
from textual.widgets import TextLog

from abacura.plugins import action
from abacura.widgets.resizehandle import ResizeHandle

class XCL(Widget):
    """Experimental CommsLog"""
    def __init__(self, id: str, name: str = ""):
        super().__init__(id=id, name=name)
        self.tl = TextLog(id="commsTL")
        
    def on_mount(self):
        pass

    def compose(self):
        yield self.tl
        yield ResizeHandle(self, "bottom")

    @action("\x1B\[1;35m<Gossip: (.*)> \'(.*)\'")
    def test_gos(self, *args, **kwargs):
        self.tl.write(f"{args[0]}: {args[1]}")
