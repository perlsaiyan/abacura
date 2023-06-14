from textual.app import ComposeResult
from textual.containers import Container

from abacura.widgets.resizehandle import ResizeHandle

from textual.widgets import Static

SIDEBAR_CONTENT="""
Character: Kensho
Mugwump delta four

Stats go here

Affects go here

"""

class Sidebar(Container):
    """Generic Sidebar"""
    def compose(self) -> ComposeResult:
        """Composes the subwidgets of a sidebar"""
        yield Static(SIDEBAR_CONTENT)
        yield ResizeHandle(self, 'right')
