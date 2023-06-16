"""Debug console widget"""
from datetime import datetime

from textual.widget import Widget
from textual.widgets import TextLog

from abacura.plugins import command
from abacura.widgets.resizehandle import ResizeHandle

class DebugDock(Widget):
    """Experimental debug window"""
    def __init__(self, id: str, name: str = ""):
        super().__init__(id=id, name=name)
        self.tl = TextLog(id="debug")

    def compose(self):
        yield ResizeHandle(self, "top")
        yield self.tl

    @command(name="debug")
    def debug(self, facility: str = "info", msg: str = ""):
        """Send output to debug window"""
        date_time = datetime.now.strftime("%m/%d/%Y, %H:%M:%S")
        self.tl.write(f"{date_time} [{facility}]: {msg}")