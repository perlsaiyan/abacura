"""A resizeable log window for communications"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import TextLog

from abacura.widgets.resizehandle import ResizeHandle

class CommsLog(Container):
    """
    Textual container for scrolling, resizable widget.
    """
    def __init__(self, id: str, name: str = ""):
        super().__init__(id=id, name=name)
        self.tl = TextLog(id="commsTL", wrap=True,auto_scroll=True)
        self.tl.can_focus = False

    def compose(self) -> ComposeResult:
        yield self.tl
        yield ResizeHandle(self, "bottom")
