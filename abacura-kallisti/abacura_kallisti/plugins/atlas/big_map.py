import time

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.timer import Timer
from textual.widgets import Button, Input, Label, RichLog, Select, Checkbox

from abacura.screens import AbacuraWindow
from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPropertyGroup, AbacuraPanel, Group, OutputColors
from abacura_kallisti.widgets import LOKMap


class BigMapWindow(AbacuraWindow):
    """Log Screen with a search box"""

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("shift+end", "scroll_end", ""),
        ("shift+home", "scroll_home", "")
    ]

    CSS_PATH = "css/kallisti.css"

    def __init__(self):
        super().__init__(title="Big Map")
        self.input = Input(id="logsearch-input", placeholder="search text")
        self.bigmap: LOKMap = LOKMap(id="bigmap", resizer=False)

    def compose(self) -> ComposeResult:
        with Grid(id="bigmap-grid") as g:
            yield self.bigmap

    def remove(self):
        self.bigmap.unregister()
        super().remove()


class BigMap(Plugin):

    @command
    def map(self):
        """
        Show a big map window
        """

        window = BigMapWindow()
        self.session.screen.mount(window)
        return
