from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, TYPE_CHECKING, Callable
import inspect

from serum import inject

if TYPE_CHECKING:
    from abacura.mud.session import Session


class Ticker:
    def __init__(self, source: object, callback: Callable, seconds: float, repeats: int = -1, name: str = ''):
        self.source: object = source
        self.callback: Callable = callback
        self.seconds: float = seconds
        self.repeats: int = repeats
        self.name: str = name
        self.last_tick = datetime.utcnow()
        self.next_tick = self.last_tick + timedelta(seconds=self.seconds)

    def tick(self) -> datetime:
        now = datetime.utcnow()
        if self.next_tick <= now and self.repeats != 0:
            # try to keep ticks aligned , so use the last target (next_tick) as the basis for adding the interval
            self.next_tick = max(now, self.next_tick + timedelta(seconds=self.seconds))
            self.last_tick = now
            self.callback()
            if self.repeats > 0:
                self.repeats -= 1

        return self.next_tick


@inject
class TickerManager:
    session: Session

    def __init__(self):
        self.tickers: List[Ticker] = []

    def register_object(self, obj: object):
        self.unregister_object(obj)  # prevent duplicates
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "ticker_seconds"):
                t = Ticker(source=obj, callback=member, seconds=getattr(member, "ticker_seconds"),
                           repeats=getattr(member, "ticker_repeats"), name=getattr(member, "ticker_name"))
                self.add(t)

    def unregister_object(self, obj: object):
        self.tickers = [t for t in self.tickers if t.source != obj]

    def add(self, ticker: Ticker):
        self.tickers.append(ticker)

    def remove(self, name: str):
        self.tickers = [t for t in self.tickers if name == '' or t.name != name]

    def process_tick(self):
        for ticker in self.tickers:
            ticker.tick()
            if ticker.repeats == 0:
                self.tickers.remove(ticker)
