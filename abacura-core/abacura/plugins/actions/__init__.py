from __future__ import annotations

import inspect
import re
from queue import PriorityQueue
from typing import TYPE_CHECKING, Callable, Match

from textual import log

from abacura.mud import OutputMessage

if TYPE_CHECKING:
    pass


class ActionError(Exception):
    pass


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

        valid_type_annotations = [str, 'str', int, float, getattr(inspect, "_empty"),
                                  Match, 'Match', OutputMessage, 'OutputMessage']

        invalid_types = [t for t in self.parameter_types if t not in valid_type_annotations]

        if invalid_types:
            raise TypeError(f"Invalid action parameter type: {callback}({invalid_types})")

    def __lt__(self, other):
        return self.priority < other.priority


class ActionManager:
    def __init__(self):
        self.actions: PriorityQueue = PriorityQueue()

    def register_object(self, obj: object):
        # self.unregister_object(obj)  # prevent duplicates
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "action_pattern"):
                act = Action(pattern=getattr(member, "action_pattern"), callback=member, source=obj,
                             flags=getattr(member, "action_flags"), color=getattr(member, "action_color"))
                self.add(act)

    def unregister_object(self, obj: object):
        self.actions.queue[:] = [a for a in self.actions.queue if a.source != obj]

    def add(self, action: Action):
        log.debug(f"Appending action '{action.name}' from '{action.source}'")
        self.actions.put(action)

    def remove(self, name: str):
        self.actions.queue[:] = [a for a in self.actions.queue if a.name != name]

    def process_output(self, message: OutputMessage):
        if type(message.message) is not str:
            return

        for act in self.actions.queue:
            s = message.message if act.color else message.stripped
            match = act.compiled_re.search(s)

            if match:
                self.initiate_callback(act, message, match)

    @staticmethod
    def initiate_callback(action: Action, message: OutputMessage, match: Match):
        g = list(match.groups())

        # perform type conversions
        if len(g) < action.expected_match_groups:
            msg = f"Incorrect # of match groups.  Expected {action.expected_match_groups}, got {g}"
            raise ActionError(msg)

        args = []

        for arg_type in action.parameter_types:
            if arg_type == Match:
                value = match
            elif arg_type == OutputMessage or arg_type == 'OutputMessage':
                value = message
            elif arg_type == int:
                try:
                    value = int(g.pop(0))
                except (ValueError, TypeError):
                    value = 0
            elif arg_type == float:
                try:
                    value = float(g.pop(0))
                except (ValueError, TypeError):
                    value = float(0)
            elif callable(arg_type) and arg_type.__name__ != '_empty':
                # fancy type conversion
                 value = arg_type(g.pop(0))
            else:
                value = g.pop(0)

            args.append(value)

        # call with the list of args
        try:
            action.callback(*args)
        except Exception as exc:
            raise ActionError(exc)
