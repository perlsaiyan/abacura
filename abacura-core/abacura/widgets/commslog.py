"""A resizeable log window for communications"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import RichLog

from abacura.widgets.resizehandle import ResizeHandle

class CommsLog(Container):
    """
    Textual container for scrolling, resizable widget.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tl = RichLog(id="commsTL", wrap=True,auto_scroll=True, max_lines=2000)
        self.tl.can_focus = False

    def compose(self) -> ComposeResult:
        yield self.tl
        yield ResizeHandle(self, "bottom")
