from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING
from rich.table import Table

from abacura.plugins import Plugin, command, CommandError

if TYPE_CHECKING:
    pass

class TickerCommand(Plugin):

    def show_tickers(self):
        tbl = Table(title="All tickers")
        tbl.add_column("Name")
        tbl.add_column("Callback")
        tbl.add_column("Source")
        tbl.add_column("Repeats", justify="right")
        tbl.add_column("Seconds", justify="right")
        tbl.add_column("Next Tick")

        for ticker in self.director.ticker_manager.tickers:
            tbl.add_row(ticker.name, ticker.callback.__qualname__, ticker.source.__class__.__name__,
                        str(ticker.repeats), format(ticker.seconds, "7.3f"), str(ticker.next_tick))

        self.output(tbl)

    @command
    def ticker(self, name: str = '', message: str = '', seconds: float = 0, repeats: int = -1,
               delete: bool = False, _list: bool = False):
        """Create/delete a ticker"""

        if _list:
            self.show_tickers()
            return

        if not name:
            raise CommandError("Must specify ticker name")

        if delete:
            self.remove_ticker(name)
            return

        if not message:
            raise CommandError("Must specify a message")

        if seconds <= 0:
            raise CommandError("Seconds must be more than 0")

        # always remove an existing ticker with this name
        self.remove_ticker(name)

        self.add_ticker(seconds=seconds, callback_fn=partial(self.session.output, msg=message),
                        repeats=repeats, name=name)
