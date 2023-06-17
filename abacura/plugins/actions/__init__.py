from __future__ import annotations

import inspect
import re
from typing import List, TYPE_CHECKING, Callable, Match

from serum import inject
from textual import log
from abacura.mud import OutputMessage

if TYPE_CHECKING:
    from abacura.mud.session import Session


class Action:
    def __init__(self, source: object, pattern: str, callback: Callable,
                 flags: int = 0, name: str = '', color: bool = False, priority: int = 0):
        self.pattern = pattern
        self.callback = callback
        self.flags = flags
        self.compiled_re = re.compile(pattern, flags)
        self.name = name
        self.color = color
        self.source = source
        self.priority = priority
        self.parameters = []

        self.parameters = list(inspect.signature(callback).parameters.values())

        self.parameter_types = [p.annotation for p in self.parameters]
        non_match_types = [Match, 'Match', OutputMessage, 'OutputMessage']
        self.expected_match_groups = len([t for t in self.parameter_types if t not in non_match_types])

        valid_type_annotations = [str, 'str', int, float, inspect._empty, Match, 'Match', OutputMessage, 'OutputMessage']
        invalid_types = [t for t in self.parameter_types if t not in valid_type_annotations]

        if invalid_types:
            raise TypeError(f"Invalid action parameter type: {callback}({invalid_types})")


@inject
class ActionManager:
    session: Session

    def __init__(self):
        self.actions: List[Action] = []

    def register_object(self, obj: object):
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "action_pattern"):
                act = Action(pattern=getattr(member, "action_pattern"), callback=member, source=obj,
                             flags=getattr(member, "action_flags"), color=getattr(member, "action_color"))
                self.add(act)

    def unregister_object(self, obj: object):
        self.actions = [a for a in self.actions if a.source != obj]

    def add(self, action: Action):
        log.debug(f"Appending action '{action.name}' from '{action.source}'")
        self.actions.append(action)

    def remove(self, name: str):
        self.actions = [a for a in self.actions if name == '' or a.name != name]

    def process_output(self, message: OutputMessage):
        if type(message.message) is not str:
            return

        act: Action
        for act in sorted(self.actions, key=lambda x: x.priority, reverse=True):
            s = message.message if act.color else message.stripped
            match = act.compiled_re.search(s)

            if match:
                self.initiate_callback(act, message, match)

    def initiate_callback(self, action: Action, message: OutputMessage, match: Match):
        g = list(match.groups())

        # perform type conversions
        if len(g) < action.expected_match_groups:
            msg = f"Incorrect # of match groups.  Expected {action.expected_match_groups}, got {g}"
            self.session.output(f"[bold red] # ERROR: {msg} {repr(action)}", markup=True)

        args = []

        for arg_type in action.parameter_types:
            if arg_type == Match:
                value = match
            elif arg_type == OutputMessage or arg_type == 'OutputMessage':
                value = message
            elif callable(arg_type) and arg_type.__name__ != '_empty':
                # fancy type conversion
                value = arg_type(g.pop(0))
            else:
                value = g.pop(0)

            args.append(value)

        # call with the list of args
        action.callback(*args)
