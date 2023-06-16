from __future__ import annotations
from serum import inject
from typing import TYPE_CHECKING, Callable
from abacura.plugins.registry import Action, Ticker, ActionRegistry, CommandRegistry, TickerRegistry
from abacura.plugins.aliases.manager import AliasManager


if TYPE_CHECKING:
    from abacura.mud.options.msdp import MSDP
    from abacura.mud.session import Session


@inject
class Plugin:
    """Generic Plugin Class"""
    session: Session
    action_registry: ActionRegistry
    command_registry: CommandRegistry
    ticker_registry: TickerRegistry
    alias_manager: AliasManager
    msdp: MSDP

    def __init__(self):
        # super().__init__()
        self.plugin_enabled = True
        self.tickers = []
        self.substitutions = []
        self.command_registry.register_object(self)
        self.action_registry.register_object(self)
        self.ticker_registry.register_object(self)

    def get_name(self):
        return self.__class__.__name__
    
    def get_help(self):
        doc = getattr(self, '__doc__', None)
        return doc

    def add_action(self, pattern: str, callback_fn: Callable, flags: int = 0, name: str = '', color: bool = False):
        act = Action(source=self, pattern=pattern, callback=callback_fn, flags=flags, name=name, color=color)
        self.action_registry.add(act)

    def remove_action(self, name: str):
        self.action_registry.remove(name)

    def add_ticker(self, seconds: float, callback_fn: Callable, repeats: int = 0, name: str = ''):
        ticker = Ticker(source=self, seconds=seconds, callback=callback_fn, repeats=repeats, name=name)
        self.ticker_registry.add(ticker)

    def remove_ticker(self, name: str):
        self.ticker_registry.remove(name)

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
