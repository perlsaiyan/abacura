from __future__ import annotations

from typing import TYPE_CHECKING, Callable
from rich.table import Table

from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPanel

if TYPE_CHECKING:
    pass


class TickerCommand(Plugin):
    """Provides #ticker command"""
    def show_tickers(self):
        rows = []
        for ticker in self.director.ticker_manager.tickers:
            callback_name = getattr(ticker.callback, "__qualname__", str(ticker.callback))
            source = ticker.source.__class__.__name__ if ticker.source else ""
            if isinstance(ticker.source, TickerCommand):
                callback_name = f"'{ticker.commands}'"

            rows.append((ticker.name, callback_name, source, ticker.repeats, ticker.seconds, ticker.next_tick))

        tbl = tabulate(rows, headers=["Name", "Callback", "Source", "Repeats", "Seconds", "Next Tick"])
        self.output(AbacuraPanel(tbl, title="Registered Tickers"))

    @command
    def ticker(self, name: str = '', commands: str = '', seconds: float = 0, repeats: int = -1, delete: bool = False):
        """
        View/Create/delete tickers

        :param name: Name of the ticker to create
        :param commands: Commands to issue each tick (separated by ;)
        :param seconds: How often to repeat the ticker
        :param repeats: How many times to repeat the ticker
        :param delete: Delete a ticker by name
        """

        if delete:
            if not name:
                raise CommandError("Must specify ticker name to delete")
            self.remove_ticker(name)
            self.output(AbacuraPanel(f"Removed ticker '{name}'", title="#ticker"))
            return

        if not name:
            self.show_tickers()
            return

        if not commands:
            raise CommandError("Must specify commands for the ticker")

        if seconds <= 0:
            raise CommandError("Seconds must be more than 0")

        # always remove an existing ticker with this name
        self.remove_ticker(name)

        def ticker_callback():
            for cmd in commands.split(";"):
                self.session.player_input(cmd, echo_color="orange1")

        self.add_ticker(seconds=seconds, callback_fn=ticker_callback, repeats=repeats, name=name, commands=commands)



