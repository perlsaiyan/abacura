from textual.app import ComposeResult
from textual.containers import Container

from abacura.widgets.resizehandle import ResizeHandle

from textual.widgets import Static

class CommsLog(Container):
    def compose(self) -> ComposeResult:
        yield Static("comms log here")
        yield ResizeHandle(self, 'bottom')
        pass
