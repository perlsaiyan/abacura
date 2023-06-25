"""Debug console widget"""
from datetime import datetime

from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import TextLog

from abacura.plugins import command, Plugin
from abacura.widgets.resizehandle import ResizeHandle

class DebugDock(Widget):
    """Experimental debug window"""
    def __init__(self, id: str, name: str = ""):
        super().__init__(id=id, name=name)
        self.tl = TextLog(id="debug")

    def compose(self):
        yield ResizeHandle(self, "top")
        yield self.tl
    
class DebugLog(Plugin):
    """Useful utilities to debug while playing"""
    def __init__(self):
        super().__init__()
        try:
            self.dl = self.session.screen.query_one("#debug", expect_type=TextLog)
        except NoMatches:
            self.dl = None


    @command(name="debuglog")
    def debug(self, facility: str = "info", msg: str = ""):
        """Send output to debug window"""
        if self.dl:
            date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            self.dl.write(f"{date_time} [{facility}]: {msg}")