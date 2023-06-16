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


class OutputLine:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def __init__(self, line: str, gag: bool):
        self.line: str = line
        if line is str:
            self.stripped = self.ansi_escape.sub('', line)
        else:
            self.stripped = line
        self.gag: bool = gag
