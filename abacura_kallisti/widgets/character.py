"""Widgets specific to legends of kallisti"""

from textual import log
from textual.app import ComposeResult
from textual.widgets import Static, TextLog, ProgressBar

class KallistiCharacter(Static):
    def compose(self) -> ComposeResult:
        yield Static()
