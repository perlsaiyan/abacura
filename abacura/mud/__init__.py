import traceback
from rich.markup import escape
from textual.widgets import TextLog
from rich.panel import Panel

class BaseSession():

    def output(self, msg, **kwargs):
        """Subclasses will handle this"""

    def show_exception(self, msg: str, exc: Exception, show_tb: bool = True):
        """Show an exception with optional traceback"""
        self.output(msg, markup=True, highlight=True)

        if show_tb:
            buf = ""
            for tb in traceback.format_tb(exc.__traceback__):
                buf += escape(tb)
            self.output(Panel(buf), markup=True, highlight=True, actionable=False)
