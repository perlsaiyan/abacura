import time

from rich.text import Text
from textual import on
from textual.app import ComposeResult, Binding
from textual.containers import Grid, Horizontal, Container
from textual.timer import Timer
from textual.widgets import Button, Input, Label, RichLog, Select, Checkbox


from abacura.plugins import Plugin, command, CommandError
from abacura.utils.ring_buffer import RingBufferLogSql
from abacura.utils.renderables import tabulate, AbacuraPropertyGroup, AbacuraPanel, Group, OutputColors, Style

class AbacuraWindow(Container):
    BINDINGS = [
        Binding("escape", "escape", "escape")
    ]

    def action_escape(self):
        self.remove()


class LogSearcher:
    def __init__(self, ring_buffer: RingBufferLogSql):
        self.ring_buffer = ring_buffer

    def search_logs(self, like: str = "", limit: int = 100, minutes_ago: int = 0, show_msdp: bool = False) -> list:
        like = like[1:] if len(like) and like[0] == "^" else "%" + like
        like = like[:-1] if len(like) and like[-1] == "$" else like + "%"

        ns_ago = int(minutes_ago) * 60 * 1000 * 1000 * 1000
        epoch_start = 0 if not minutes_ago else (time.time_ns() - ns_ago)

        clauses = [] if show_msdp else [r"stripped not like '!MSDP%'"]
        clauses = [""] + clauses if len(clauses) else []
        exclude_clause = " and ".join(clauses)

        logs = self.ring_buffer.query(like, clause=exclude_clause, limit=limit, epoch_start=epoch_start)
        return logs


class LogSearchWindow(AbacuraWindow):
    """Log Screen with a search box"""

    BINDINGS = [
        ("pageup", "pageup", "PageUp"),
        ("pagedown", "pagedown", "PageDown"),
        ("shift+end", "scroll_end", ""),
        ("shift+home", "scroll_home", "")
    ]

    # CSS_PATH = "css/kallisti.css"
    def __init__(self, searcher: LogSearcher, find: str = "%", show_msdp: bool = False):
        super().__init__()
        self.searcher = searcher
        self.richlog = RichLog(id="logsearch-log")
        self.input = Input(id="logsearch-input", placeholder="search text")
        if find != "%":
            self.input.value = find
        row_options = [(" 100 rows", 100), ("1000 rows", 1000)]
        self.row_limit = Select[int](row_options, id="logsearch-rows", value=100)
        self.msdp_checkbox = Checkbox("MSDP", value=show_msdp)
        self.footer: Label = Label("", id="logsearch-footer")

        self.call_after_refresh(self.run_search, find)
        self.populate_timer: Timer | None = None

        self.richlog.can_focus = False
        self.msdp_checkbox.can_focus = False
        self.row_limit.can_focus = False


    async def run_search(self, find: str = '%'):
        if self.populate_timer:
            self.populate_timer.stop()
        start = time.monotonic()
        results = self.searcher.search_logs(find, limit=self.row_limit.value, show_msdp=self.msdp_checkbox.value)
        elapsed = time.monotonic() - start
        self.call_later(self.display_results, results, elapsed)

    async def display_results(self, results: list, elapsed: float = 0):
        self.footer.refresh()
        # with self.app.batch_update():
        with self.screen.app.batch_update():
            self.richlog.clear()
            self.richlog.auto_scroll = True
            if len(results):
                for lt, lc, ll in results:
                    self.richlog.write(Text.from_ansi(f"{lt:15} {lc:>6} {ll[:300]}"))
            else:
                self.richlog.write(Text("No results found", style="red"))

            self.footer.renderable = Text(f"{len(results)} lines returned in {elapsed:5.3f}s")
            self.footer.refresh()

    def compose(self) -> ComposeResult:
        with Grid(id="logsearch-grid") as g:
            g.border_title = "Log Search"
            with Horizontal():
                yield Label("Search: ", id="logsearch-label")
                yield self.input

            with Horizontal():
                yield self.row_limit
                yield self.msdp_checkbox

            yield Button("Close", variant="primary", id="logsearch-close")
            yield Label("Search Results", id="logsearch-results-label")
            yield self.richlog
            yield self.footer

        self.screen.set_focus(self.input)

    @on(Checkbox.Changed)
    async def checkbox_changed(self, _event: Checkbox.Changed) -> None:
        await self.run_search(self.input.value)

    @on(Select.Changed)
    async def select_changed(self, _event: Select.Changed) -> None:
        await self.run_search(self.input.value)

    @on(Input.Changed)
    async def on_input_changed(self, event: Input.Changed):
        async def run_search():
            await self.run_search(event.value)

        if self.populate_timer:
            self.populate_timer.stop()

        self.populate_timer = self.set_timer(0.40, run_search)

    async def on_input_submitted(self, event: Input.Submitted):
        if self.populate_timer:
            self.populate_timer.stop()

        await self.run_search(event.value)

    def on_button_pressed(self, _event: Button.Pressed) -> None:
        self.remove()

    def action_pageup(self) -> None:
        self.richlog.scroll_page_up(duration=0.3)

    def action_pagedown(self) -> None:
        self.richlog.scroll_page_down(duration=0.3)

    def action_scroll_home(self) -> None:
        self.richlog.scroll_home(duration=0.3)

    def action_scroll_end(self) -> None:
        self.richlog.scroll_end(duration=0.3)

class LogSearch(Plugin):

    @command
    def log(self, find: str = "%", limit: int = 40, dump: bool = False, msdp: bool = False):
        """
        Search output log and show results in a window

        :param find: Search for text using sql % wildcard style
        :param limit: limit the number of log entries returned
        :param msdp: Show msdp values
        :param dump: dump output to mud instead of bringing up new window
        """

        if self.session.ring_buffer is None:
            raise CommandError("No output log ring buffer configured")

        ls = LogSearcher(self.session.ring_buffer)

        if not dump:
            window = LogSearchWindow(ls, find, msdp)
            self.session.screen.mount(window)
            return

        logs = ls.search_logs(find, limit, show_msdp=msdp)
        logs = [(t, c, Text.from_ansi(l).markup) for t, c, l in logs]

        pview = AbacuraPropertyGroup({"Find": find, "Limit": limit, "MSDP": msdp}, title="Properties")

        if len(logs) == 0:
            results = Text.assemble(("Results\n\n", OutputColors.section), ("No logs found", ""))
        else:
            headers = ["Time", "Context", "Line"]
            caption = f" {len(logs)} logs found"
            from rich.table import Table
            tbl = Table()
            tbl.add_column("Time")
            tbl.add_column("Context")
            tbl.add_column("Line")
            for row in logs:
                tbl.add_row(*row)

            results = tabulate(logs, headers=headers, title="Results", caption=caption, expand=True)
 #           results = tbl

        self.output(AbacuraPanel(Group(pview, Text(), results), "Log Search", expand=True))

        # self.output(tbl)