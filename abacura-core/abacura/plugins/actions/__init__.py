from __future__ import annotations

import inspect
import re
from queue import PriorityQueue
from typing import TYPE_CHECKING, Callable, Match

from textual import log

from abacura.mud import OutputMessage
from abacura.utils.timer import Timer

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

        # Add fast pre-filtering hint
        self.quick_check = self._extract_quick_check(pattern)

        self.parameters = list(inspect.signature(callback).parameters.values())

        self.parameter_types = [p.annotation for p in self.parameters]
        non_match_types = [Match, 'Match', OutputMessage, 'OutputMessage']
        self.expected_match_groups = len([t for t in self.parameter_types if t not in non_match_types])

        valid_type_annotations = [str, 'str', int, float, getattr(inspect, "_empty"),
                                  Match, 'Match', OutputMessage, 'OutputMessage']

        invalid_types = [t for t in self.parameter_types if t not in valid_type_annotations]

        if invalid_types:
            raise TypeError(f"Invalid action parameter type: {callback}({invalid_types})")

    def _extract_quick_check(self, pattern: str) -> str:
        """Extract a literal string that must be present for the regex to match"""
        # Remove anchors
        clean = pattern.replace('^', '').replace('$', '')
        
        # Handle escaped characters - remove backslashes and the char after
        import re as regex_module
        clean = regex_module.sub(r'\\(.)', r'\1', clean)
        
        # Get text before first regex metacharacter  
        for char in ['(', '[', '*', '+', '?', '.', '|']:
            if char in clean:
                clean = clean[:clean.index(char)]
                break
        
        # Clean up whitespace and only use if meaningful
        clean = clean.strip()
        return clean if len(clean) > 3 else ''

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

        # Count lines processed for accurate performance metrics
        Timer.timers.setdefault("lines_processed", 0)
        Timer.timers["lines_processed"] += 1

        # Pre-compute both strings once instead of repeatedly in the loop
        color_text = message.message
        stripped_text = message.stripped
        
        with Timer("action_processing_total"):
            action_count = 0
            quick_check_count = 0
            regex_check_count = 0
            match_count = 0
            
            # Pre-extract all object attributes to eliminate expensive lookups in hot loop
            with Timer("action_preparation"):
                action_data = [(act.compiled_re, act.quick_check, act.color, act) 
                              for act in self.actions.queue]
            
            for compiled_re, quick_check, use_color, action in action_data:
                action_count += 1
                s = color_text if use_color else stripped_text
                
                # Fast pre-filtering - skip expensive regex if simple string not present
                if quick_check:
                    quick_check_count += 1
                    if quick_check not in s:
                        continue
                
                # Only do expensive regex if quick check passed (or no quick check available)
                regex_check_count += 1
                match = compiled_re.search(s)
                
                if match:
                    match_count += 1
                    self.initiate_callback(action, message, match)
                        
            # Track detailed performance metrics
            Timer.timers.setdefault("total_action_checks", 0)
            Timer.timers.setdefault("total_quick_checks", 0)
            Timer.timers.setdefault("total_regex_checks", 0)
            Timer.timers.setdefault("total_matches", 0)
            Timer.timers["total_action_checks"] += action_count
            Timer.timers["total_quick_checks"] += quick_check_count
            Timer.timers["total_regex_checks"] += regex_check_count
            Timer.timers["total_matches"] += match_count

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
