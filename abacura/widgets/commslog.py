"""
A resizeable log window for communications
"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from abacura.widgets.resizehandle import ResizeHandle



class CommsLog(Container):
    """
    Textual container for what will be a scrolling, resizable widget.
    We'll probably dock it at the top of the screen but layout choices is the user's call.
    """
    def compose(self) -> ComposeResult:
        yield Static("comms log here")
        yield ResizeHandle(self, 'bottom')
        pass
