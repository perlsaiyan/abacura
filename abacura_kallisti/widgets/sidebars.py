from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Static, ProgressBar
import random
from textual import log
from textual.app import App, ComposeResult
from textual.containers import Center, Middle
from textual.timer import Timer
from textual.widgets import Footer, ProgressBar

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.resizehandle import ResizeHandle

from abacura_kallisti.widgets import KallistiCharacter

class LOKLeft(Sidebar):
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "right")
        with Container(id="leftsidecontainer", classes="SidebarContainer"):
            yield KallistiCharacter(id="kallisticharacter")
            yield Static("Affects", classes="WidgetTitle")
            yield Static("[green]Goo [white]3   [green]Wims [white]5")
            yield Static("Mount", classes="WidgetTitle")
            yield Static("Bephus the Dragon [100/100/100]")
            yield Static("Levels and Remort", classes="WidgetTitle")
            yield Static("[green]Total: [white]20  [green]In Class: 0")
            pb = ProgressBar(total= 100, show_bar=True, show_percentage=True, show_eta=True, id="RemortProgress")
            yield IndeterminateProgressBar()
            pb.advance(50)
            
class LOKRight(Sidebar):
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "left")
        with Container(id="rightsidecontainer", classes="SidebarContainer"):
            yield Static("Pending Sixel Support :)", classes="Map")
            yield Static("Zone", classes="WidgetTitle")
            yield Static("[bright blue]Ruins of DongDong\n[green]Level: [white]75-100")
            yield Static("Action Queues", classes="WidgetTitle")
            yield Static("[green]Priority: [white]0 [green]Heal: [white]0  [green]Any: [white]0\n" + \
                         "[green]  Combat: [white]0 [green] NCO: [white]0 [green]Move: [white]0")


class IndeterminateProgressBar(Widget):

    progress_timer: Timer
    """Timer to simulate progress happening."""

    def compose(self) -> ComposeResult:
        yield Static("Remort Progress", classes="WidgetTitle")
        yield ProgressBar(show_eta=True, show_percentage=True)
        

    def on_mount(self) -> None:
        """Set up a timer to simulate progess happening."""
        self.progress_timer = self.set_interval(1 / 10, self.make_progress, pause=True)
        self.action_start()

    def make_progress(self) -> None:
        """Called automatically to advance the progress bar."""
        log("Making progress")
        pb = self.query_one(ProgressBar)
        pb.progress = random.randint(1,99)
        if pb.percentage == 100:
            pb.update(total=pb.total + pb.total)
            pb.progress = 0

    def action_start(self) -> None:
        """Start the progress tracking."""
        self.query_one(ProgressBar).update(total=100)
        self.progress_timer.resume()
