from __future__ import annotations
import inspect
import re
from serum import inject
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from textual.app import App
    from abacura.mud.session import Session
    from abacura.plugins.plugin import PluginManager


@inject
class Plugin:
    """Generic Plugin Class"""
    app: App
    session: Session
    manager: PluginManager

    def __init__(self):
        super().__init__()
        self.plugin_enabled = True

    def get_name(self):
        return self.__class__.__name__
    
    def get_help(self):
        doc = getattr(self, '__doc__', None)
        return doc

    def evaluate_command_argument(self, parameter: inspect.Parameter, submitted_value: str):

        if parameter.annotation == int:
            return int(submitted_value)

        if parameter.annotation == float:
            return float(submitted_value)

        return submitted_value


def ticker(seconds: float):
    def add_ticker(ticker_fn):
        ticker_fn.ticker_interval = seconds
        return ticker_fn

    return add_ticker


def action(regex: str, color: bool = False):
    def add_action(action_fn):
        action_fn.action_re = regex
        action_fn.action_re_compiled = re.compile(regex)
        action_fn.action_color = color
        return action_fn
    
    return add_action


def command(function=None, name: str = ''):
    def add_command(fn):
        fn.command = True
        fn.command_name = name or fn.__name__

        return fn

    if function:
        return add_command(function)

    return add_command
