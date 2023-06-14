from __future__ import annotations
import inspect
from serum import inject
from typing import TYPE_CHECKING, Callable


if TYPE_CHECKING:
    from textual.app import App
    from abacura.mud.session import Session
    from abacura.plugins.plugin import PluginManager, ActionRegistry, Action


@inject
class Plugin:
    """Generic Plugin Class"""
    app: App
    session: Session
    manager: PluginManager
    action_registry: ActionRegistry

    def __init__(self):
        super().__init__()
        self.plugin_enabled = True
        self.tickers = []
        self.substitutions = []

    def get_name(self):
        return self.__class__.__name__
    
    def get_help(self):
        doc = getattr(self, '__doc__', None)
        return doc

    def add_action(self, pattern: str, callback_fn: Callable, flags: int = 0, name: str = '', color: bool = False):
        act = Action(pattern=pattern, callback=callback_fn, flags=flags, name=name, color=color)
        self.action_registry.add(act)

    def remove_action(self, name: str):
        self.action_registry.remove(name)

    def add_ticker(self, seconds: int, callback_fn: Callable, repeat: int = 0, name: str = ''):
        pass

    def remove_ticker(self, name: str):
        pass

    def add_substitute(self, pattern: str, repl: str, name: str = ''):
        pass

    def remove_substitute(self, name: str):
        pass

    def evaluate_command_argument(self, parameter: inspect.Parameter, submitted_value: str):
        if parameter.annotation == int:
            return int(submitted_value)

        if parameter.annotation == float:
            return float(submitted_value)

        return submitted_value


def action(pattern: str, flags: int = 0, color: bool = False):
    def add_action(action_fn):
        action_fn.action_pattern = pattern
        action_fn.action_color = color
        action_fn.action_flags = flags
        return action_fn
    
    return add_action


def command(function=None, name: str = ''):
    def add_command(fn):
        fn.command_name = name or fn.__name__

        return fn

    if function:
        return add_command(function)

    return add_command
