import traceback
from rich.markup import escape
from textual.widgets import TextLog
from rich.panel import Panel

class BaseSession():
    tl: TextLog
    

    def show_exception(self, msg: str, e: Exception):
        buf = ""
        for tb in traceback.format_tb(e.__traceback__):
            buf += escape(tb)
        self.tl.markup = True
        self.tl.highlight = True
        self.tl.write(msg)
        self.tl.write(Panel(buf))
        self.tl.markup = False
        self.tl.highlight = False
    pass