import traceback
from rich.markup import escape
from rich.panel import Panel
import re


class BaseSession:

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


class OutputMessage:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def __init__(self, message: str, gag: bool):
        self.message: str = message
        if type(message) is str:
            self.stripped = self.ansi_escape.sub('', message)
        else:
            self.stripped = message
        self.gag: bool = gag
