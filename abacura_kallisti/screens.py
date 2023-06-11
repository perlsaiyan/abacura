"""Legends of Kallisti Test Screen"""

from abacura import Header, SessionScreen, InputBar, AbacuraFooter
from abacura.inspector import Inspector
from abacura.widgets.sidebar import Sidebar
from abacura.widgets.commslog import CommsLog

from textual import log
from textual.app import ComposeResult
from textual.containers import Container, Center, Middle
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Static, TextLog, ProgressBar

from rich.progress import Progress, BarColumn

class UpsideDownScreen(SessionScreen):
    """Screen with input bar at top"""
    BINDINGS = [("ctrl+p", "craft", "Craft"),
                ("f2", "toggle_sidebar", "Toggle Sidebar"),
            ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        yield Sidebar(id="leftsidebar")
        with Container(id="app-grid"):
            yield CommsLog(id="commslog", name="commslog")
            with Container(id="mudoutputs"):
                
                yield TextLog(
                    highlight=False, markup=False, wrap=False, name=self.tlid, classes="mudoutput", id=self.tlid
                    )
            yield InputBar()
        inspector = Inspector()
        inspector.display = False
        yield inspector

        yield AbacuraFooter()

    def action_craft(self) -> None:
        sidebar = self.query_one("#leftsidebar", expect_type=Sidebar)
        sidebar.mount(CraftingWidget(id="craftingwidget"))
        cw = sidebar.query_one(CraftingWidget)
        cw.display = "block"
    
    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#leftsidebar", expect_type=Sidebar)
        sidebar.display = not sidebar.display

class IndeterminateProgress(Static):
    def __init__(self):
        super().__init__("")
        self._bar = Progress(BarColumn())  
        self._bar.add_task("", total=None)  

    def on_mount(self) -> None:
        # When the widget is mounted start updating the display regularly.
        self.update_render = self.set_interval(
            1 / 60, self.update_progress_bar
        )  

    def update_progress_bar(self) -> None:
        self.update(self._bar)  

class CraftingWidget(Static):
    def compose(self) -> ComposeResult:
        yield Static(f"Leatherworking 1/100", id="CWLabel")
        yield IndeterminateProgressBar()
        self.display = "block"
        self.styles.width = self.parent.styles.width

    def on_mount(self) -> None:
        self.query_one(IndeterminateProgressBar).action_start()

    def on_indeterminate_progress_bar_finished(self, finished: bool) -> None:
        self.remove()
    
    def on_indeterminate_progress_bar_updated(self, message) -> None:
        static = self.query_one("#CWLabel")
        static.update(f"Leatherworking {int(message.current)}/{message.total} {self.parent.styles.width}")

class IndeterminateProgressBar(Static):
    BINDINGS = [("ctrl+s", "start", "Start")]

    progress_timer: Timer
    """Timer to simulate progress happening."""

    class Finished(Message):

        def __init__(self, finished: bool) -> None:
            self.finished = finished
            super().__init__()

    class Updated(Message):

        def __init__(self, current: float, total: int) -> None:
            self.current = current
            self.total = total
            super().__init__()

    def compose(self) -> ComposeResult:
        pb = ProgressBar(total=100, show_eta=True, show_percentage=False)
        with Center():
            with Middle():
                yield pb

    def on_mount(self) -> None:
        """Set up a timer to simulate progess happening."""
        self.progress_timer = self.set_interval(1 / 10, self.make_progress, pause=True)

    def make_progress(self) -> None:
        """Called automatically to advance the progress bar."""
        pb = self.query_one(ProgressBar)
        pb.advance(1)
        self.post_message(self.Updated(current = pb.progress, total= pb.total))
        log(f"WIDTH IS {self.parent.parent.styles.width}")
        if pb.progress == pb.total:
            self.post_message(self.Finished(True))

    def action_start(self) -> None:
        """Start the progress tracking."""

        self.query_one(ProgressBar).update(progress = 0)
        self.progress_timer.reset()
        
