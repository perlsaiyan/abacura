from __future__ import annotations
import inspect
import re
from serum import inject
from typing import TYPE_CHECKING, Callable, Match


if TYPE_CHECKING:
    from textual.app import App
    from abacura.mud.session import Session
    from abacura.plugins.plugin import PluginManager


class ActionProcessor:
    def __init__(self, pattern: str, callback: Callable, flags: int = 0, name: str = '', color: bool = False):
        self.pattern = pattern
        self.callback = callback
        self.flags = flags
        self.compiled_re = re.compile(pattern, flags)
        self.name = name

        self.parameters = list(inspect.signature(callback).parameters.values())
        self.parameter_types = [p.annotation for p in self.parameters]
        self.expected_match_groups = len([t for t in self.parameter_types if t != Match])

        valid_type_annotations = [str, int, float, inspect._empty, Match]
        invalid_types = [t for t in self.parameter_types if t not in valid_type_annotations]

        if invalid_types:
            raise TypeError(f"Invalid action parameter type: {callback}({invalid_types})")

    def process(self, m: Match):
        g = m.groups()

        # perform type conversions
        if len(g) < self.expected_match_groups:
            raise TypeError(f"Incorrect # of match groups.  Expected {self.expected_match_groups}, got {g}")

        args = []

        for arg_type, value in zip(self.parameter_types, m.groups()):
            if arg_type == Match:
                value = m
            elif callable(arg_type) and arg_type.__name__ != '_empty':
                # fancy type conversion
                value = arg_type(value)

            args.append(value)

        # call with the list of args
        self.callback(*args)


@inject
class Plugin:
    """Generic Plugin Class"""
    app: App
    session: Session
    manager: PluginManager

    def __init__(self):
        super().__init__()
        self.plugin_enabled = True
        self.tickers = []
        self.actions = []
        self.substitutions = []

    def inspect_methods(self):
        for name, member in inspect.getmembers(self, callable):
            if hasattr(member, "action_pattern"):
                act = ActionProcessor(pattern=getattr(member, "action_pattern"), callback=member,
                                      flags=getattr(member, "action_flags"), color=getattr(member, "action_color"))
                self.actions.append(act)

    def get_name(self):
        return self.__class__.__name__
    
    def get_help(self):
        doc = getattr(self, '__doc__', None)
        return doc

    def add_action(self, pattern: str, callback_fn: Callable, flags: int = 0, name: str = ''):
        self.actions.append(ActionProcessor(pattern, callback_fn, flags, name))

    def remove_action(self, name: str):
        self.actions = [a for a in self.actions if name == '' or a.name != name]

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
