"""Main screen and widgets for abacura"""
from __future__ import annotations

# TODO: screen and widget definitions should go under the hierarchy, not in __init__
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, RichLog
from textual import events

from abacura.widgets import CommsLog, InputBar
from abacura.widgets.debug import DebugDock
from abacura.widgets.footer import AbacuraFooter
from abacura.widgets.sidebar import Sidebar

if TYPE_CHECKING:
    from abacura.mud.session import Session


class SessionRichLog(RichLog):

    def on_resize(self, _e: events.Resize):
        # animate this to reduce "flicker" when toggling commslog, debuglog
        self.scroll_end(duration=0.1)

    def viewing_end(self) -> bool:
        return self.scroll_offset.y >= self.virtual_size.height - self.content_size.height


class SessionScreen(Screen):
    """Default Screen for sessions"""

    MAX_LINES: int = 10000

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("shift+end", "scroll_end", ""),
        ("shift+home", "scroll_home", ""),
        ("f2", "toggle_sidebar", "F2"),
        ("f3", "toggle_commslog", "F3")
    ]

    AUTO_FOCUS = "InputBar"

    def __init__(self, name: str, session: Session):
        super().__init__()

        self.session = session
        self.id = f"screen-{name}"
        self.tlid = f"output-{name}"
        # TODO: wrap should be a config file field option
        self.tl: SessionRichLog = SessionRichLog(highlight=False, markup=False, wrap=True, auto_scroll=False,
                                                 name=self.tlid, classes="mudoutput", id=self.tlid,
                                                 max_lines=self.MAX_LINES)
        self.tl.can_focus = False
        self.footer = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the session"""
        commslog = CommsLog(id="commslog", name="commslog")
        commslog.display = False
        yield Header(show_clock=True, name="Abacura", id="masthead", classes="masthead")
        yield commslog

        with Container(id="app-grid"):
            yield Sidebar(id="sidebar", name="sidebar")
            with Container(id="mudoutputs"):
                yield self.tl
            yield InputBar(id="playerinput")
        yield AbacuraFooter(id="footer")
        if self.session.abacura.inspector:
            from abacura.widgets._inspector import Inspector
            inspector = Inspector()
            inspector.display = False
            yield inspector
        debugger = DebugDock(id="debugger")
        debugger.display = False
        yield debugger

    def on_mount(self) -> None:
        """Screen is mounted, launch it"""
        self.session.launch_screen()

    async def on_input_bar_user_command(self, command: InputBar.UserCommand) -> None:
        """Handle user input from InputBar"""
        self.session.player_input(command.command, gag=command.password)

    def action_toggle_dark(self) -> None:
        """Dark mode"""
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

## session.abacura.screen.query_one("app-grid").query_one("playerinput").password

    def action_toggle_commslog(self) -> None:
        commslog = self.query_one("#commslog")
        commslog.display = not commslog.display
        self.refresh()

    def action_pageup(self) -> None:
        # self.tl.auto_scroll = False
        # self.tl.max_lines = self.MAX_LINES * 2

        self.tl.scroll_page_up(duration=0.3)

    def action_pagedown(self) -> None:
        # if self.tl.scroll_offset.y >= self.tl.virtual_size.height - self.tl.content_size.height:
            # self.tl.auto_scroll = True
            # self.tl.max_lines = self.MAX_LINES

        self.tl.scroll_page_down(duration=0.3)

    def action_scroll_home(self) -> None:
        # self.tl.auto_scroll = False
        # self.tl.max_lines = self.MAX_LINES * 2

        self.tl.scroll_home(duration=0.3)

    def action_scroll_end(self) -> None:
        # self.tl.auto_scroll = True
        # self.tl.max_lines = self.MAX_LINES

        self.tl.scroll_end(duration=0.3)


class AbacuraWindow(Container):
    BINDINGS = [
        ("escape", "escape", "Close Window")
    ]

    def __init__(self, title="Window", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.close_color = "red"
        self.border_title = f"[red] X [/red][bold cyan]{title}"

    def action_escape(self):
        self.remove()

    def on_click(self, event: events.Click):
        # check if the click was on the border, on the "close" button [ X ] color
        if event.y == 0 and event.style.color and event.style.color.name == self.close_color:
            self.remove()
