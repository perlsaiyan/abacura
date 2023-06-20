from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from serum import inject

from abacura.plugins.actions import Action
from abacura.plugins.director import Director
from abacura.plugins.tickers import Ticker

if TYPE_CHECKING:
    from abacura.mud.options.msdp import MSDP
    from abacura.mud.session import Session
    from abacura.config import Config


class ContextProvider:

    def __init__(self, config: Config, session_name: str):
        pass

    def get_injections(self) -> dict:
        return {}


@inject
class Plugin:
    """Generic Plugin Class"""
    session: Session
    director: Director
    core_msdp: MSDP

    def __init__(self):
        # super().__init__()
        self.plugin_enabled = True
        self.tickers = []
        self.substitutions = []
        self.director.register_object(self)
        self.output = self.session.output

    def get_name(self):
        return self.__class__.__name__
    
    def get_help(self):
        doc = getattr(self, '__doc__', None)
        return doc

    def add_action(self, pattern: str, callback_fn: Callable, flags: int = 0, name: str = '', color: bool = False):
        act = Action(source=self, pattern=pattern, callback=callback_fn, flags=flags, name=name, color=color)
        self.director.action_manager.add(act)

    def remove_action(self, name: str):
        self.director.action_manager.remove(name)

    def add_ticker(self, seconds: float, callback_fn: Callable, repeats: int = 0, name: str = ''):
        ticker = Ticker(source=self, seconds=seconds, callback=callback_fn, repeats=repeats, name=name)
        self.director.ticker_manager.add(ticker)

    def remove_ticker(self, name: str):
        self.director.ticker_manager.remove(name)

    def add_substitute(self, pattern: str, repl: str, name: str = ''):
        pass

    def remove_substitute(self, name: str):
        pass


def action(pattern: str, flags: int = 0, color: bool = False, priority: int = 0):
    def add_action(action_fn):
        action_fn.action_pattern = pattern
        action_fn.action_color = color
        action_fn.action_flags = flags
        action_fn.action_priority = priority
        return action_fn
    
    return add_action


def command(function=None, name: str = ''):
    def add_command(fn):
        fn.command_name = name or fn.__name__
        return fn

    if function:
        return add_command(function)

    return add_command
