from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from serum import Context

from abacura.plugins.actions import Action
from abacura.plugins.director import Director
from abacura.plugins.tickers import Ticker
from abacura.plugins.commands import CommandError
from abacura.plugins.task_queue import QueueManager
from abacura.utils.fifo_buffer import FIFOBuffer
from abacura.mud import OutputMessage

if TYPE_CHECKING:
    from abacura.mud.options.msdp import MSDP
    from abacura.mud.session import Session
    from abacura.config import Config


class ContextProvider:

    def __init__(self, config: Config, session_name: str):
        pass

    def get_injections(self) -> dict:
        return {}


class Plugin:
    """Generic Plugin Class"""
    _context: Context

    def __init__(self):
        # super().__init__()
        self.session: Session = self._context['session']
        self.config: Config = self._context['config']
        self.director: Director = self._context['director']
        self.core_msdp: MSDP = self._context['core_msdp']
        self.cq: QueueManager = self._context['cq']
        self.output_history: FIFOBuffer[OutputMessage] = self._context['buffer']
        self.output = self.session.output
        self.debuglog = self.session.debuglog
        self.dispatch = self.director.event_manager.dispatch
        self.register_actions = True

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

    def add_ticker(self, seconds: float, callback_fn: Callable, repeats: int = -1, name: str = '', commands: str = ''):
        t = Ticker(source=self, seconds=seconds, callback=callback_fn, repeats=repeats, name=name, commands=commands)
        self.director.ticker_manager.add(t)

    def remove_ticker(self, name: str):
        self.director.ticker_manager.remove(name)

    def add_substitute(self, pattern: str, repl: str, name: str = ''):
        pass

    def remove_substitute(self, name: str):
        pass

    def send(self, message: str, raw: bool = False, echo_color: str = 'orange1'):
        self.session.send(message, raw=raw, echo_color=echo_color)


def action(pattern: str, flags: int = 0, color: bool = False, priority: int = 0):
    def add_action(action_fn):
        action_fn.action_pattern = pattern
        action_fn.action_color = color
        action_fn.action_flags = flags
        action_fn.action_priority = priority
        return action_fn
    
    return add_action


def command(function=None, name: str = '', hide: bool = False):
    def add_command(fn):
        fn.command_name = name or fn.__name__
        fn.command_hide = hide
        return fn

    if function:
        return add_command(function)

    return add_command


def ticker(seconds: int, repeats=-1, name=""):
    def add_ticker(fn):
        fn.ticker_seconds = seconds
        fn.ticker_repeats = repeats
        fn.ticker_name = name
        return fn

    return add_ticker
