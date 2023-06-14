from __future__ import annotations

import inspect
import re
import shlex
from datetime import datetime, timedelta
from typing import List, Dict, TYPE_CHECKING, Callable, Match

from rich.markup import escape
from serum import inject
from textual import log

if TYPE_CHECKING:
    from abacura.mud.session import Session


class Ticker:
    def __init__(self, source: object, callback: Callable, seconds: int, repeats: int = -1, name: str = ''):
        self.source = source
        self.callback = callback
        self.seconds = seconds
        self.repeats = repeats
        self.name = name
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


class Command:
    def __init__(self, source: object, callback: Callable, name: str):
        self.callback = callback
        self.name = name
        self.source = source

    def execute(self, command_arguments: str):
        submitted_arguments = shlex.split(command_arguments)

        submitted_options = [s.strip("-") for s in submitted_arguments if s.startswith("-")]
        submitted_arguments = [s for s in submitted_arguments if not s.startswith("-")]

        d = self.evaluate_options(submitted_options)
        if 'help' in d:
            return self.get_help()

        d.update(self.evaluate_arguments(submitted_arguments, command_arguments))

        return self.callback(**d)

    def evaluate_argument(self, parameter: inspect.Parameter, submitted_value: str):
        if parameter.annotation == int:
            return int(submitted_value)

        if parameter.annotation == float:
            return float(submitted_value)

        return submitted_value

    def evaluate_arguments(self, submitted_arguments: List[str], cmd_str: str) -> Dict:
        """evaluate arguments to command functions"""
        command_parameters = self.get_parameters()
        evaluated_args = {}

        for parameter in command_parameters:
            if parameter.default is inspect.Parameter.empty and len(submitted_arguments) == 0:
                raise AttributeError(f"Missing argument {parameter.name}")

            if len(submitted_arguments) > 0:
                if parameter.name.lower() == 'text':
                    value = cmd_str
                    submitted_arguments = []
                else:
                    value = submitted_arguments.pop(0)
            else:
                value = parameter.default

            evaluated_args[parameter.name] = self.evaluate_argument(parameter, value)

        return evaluated_args

    def evaluate_options(self, submitted_options: List[str]) -> dict[str, any]:
        """evaluate options to command functions"""
        command_options = self.get_boolean_options()

        for co in submitted_options:
            matched_options = [k for k in command_options.keys() if k.startswith(co.lower())]
            if co.lower() in ['h', 'help', '?']:
                command_options['help'] = True
            elif len(matched_options) == 1:
                option_name = matched_options[0]
                command_options[option_name] = True
            elif not self.pass_full_command_text():
                # don't throw an error if the command will take in the full text.  As in @@ 2 - 1
                msg = "Ambiguous option: " if len(matched_options) > 1 else "Invalid option: "
                raise NameError(msg + co)
        return command_options

    def pass_full_command_text(self) -> bool:
        return any([a for a in self.get_parameters() if a.name.lower() == 'text'])

    def get_parameters(self) -> List[inspect.Parameter]:
        parameters = inspect.signature(self.callback).parameters.values()
        return [p for p in parameters if p.annotation != bool]

    def get_boolean_options(self):
        parameters = inspect.signature(self.callback).parameters.values()
        return {p.name: p.default for p in parameters if p.annotation == bool}

    def get_help(self):
        help_text = []

        doc = getattr(self.callback, '__doc__', None)

        options = self.get_boolean_options()
        option_help = ['--%s' % k for k in options.keys()]

        parameters = self.get_parameters()
        parameter_help = []
        for parameter in parameters:
            if parameter.default is inspect.Parameter.empty:
                parameter_help.append(parameter.name)
            else:
                parameter_help.append(f"[{parameter.name}]")

        if doc is not None:
            help_text.append(doc + "\n")

        help_text.append(f"Usage: {self.name} {' '.join(option_help + parameter_help)}")

        return "\n".join(help_text)


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

        self.parameters = list(inspect.signature(callback).parameters.values())
        self.parameter_types = [p.annotation for p in self.parameters]
        self.expected_match_groups = len([t for t in self.parameter_types if t != Match])

        valid_type_annotations = [str, int, float, inspect._empty, Match]
        invalid_types = [t for t in self.parameter_types if t not in valid_type_annotations]

        if invalid_types:
            raise TypeError(f"Invalid action parameter type: {callback}({invalid_types})")


@inject
class TickerRegistry:
    session: Session

    def __init__(self):
        self.tickers: List[Ticker] = []

    def register_object(self, obj: object):
        pass

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


@inject
class CommandRegistry:
    session: Session

    def __init__(self):
        self.commands: List[Command] = []

    def register_object(self, obj: object):
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "command_name"):
                log(f"Appending command function '{member.command_name}'")
                self.commands.append(Command(obj, member, member.command_name))

    def unregister_object(self, obj: object):
        self.commands = [a for a in self.commands if a.source != obj]

    def execute_command(self, command_line: str) -> bool:
        if not len(command_line):
            return False

        # remove leading @
        s = command_line[1:].rstrip("\n").split(" ")
        submitted_command = s[0]
        submitted_args = "" if len(s) == 1 else " ".join(s[1:])

        if submitted_command == '':
            submitted_command = 'help'

        # look for partial matches and exact matches
        starts = [cmd for cmd in self.commands if cmd.name.lower().startswith(submitted_command.lower())]
        exact_matches = [cmd for cmd in self.commands if cmd.name.lower() == submitted_command.lower()]

        if len(exact_matches) == 1:
            # use the exact match if we have 1
            command = exact_matches[0]
        elif len(starts) == 1:
            # use the partial match if there is only 1
            command = starts[0]
        elif len(starts) == 0:
            error_msg = f"Unknown Command {submitted_command}"
            self.session.output(f"[orange][italic]> {escape(error_msg)}", markup=True, highlight=True)
            return False
        else:
            matches = ", ".join([cmd.name for cmd in starts])
            error_msg = f"Ambiguous command '{submitted_command}' [{matches}]"
            self.session.output(f"[orange][italic]> {escape(error_msg)}", markup=True, highlight=True)
            return False

        try:
            self.session.output(f"[green][italic]> {escape(command_line)}", markup=True, highlight=True)
            message = command.execute(submitted_args)
            if message:
                self.session.output(message)

        except AttributeError as e:
            self.session.show_exception(f"[bold red] # ERROR: {command.name}: {repr(e)}", e)
            self.session.output(f"[gray][italic]> {escape(command.get_help())}", markup=True, highlight=True)
            return False

        except (ValueError, NameError) as e:
            self.session.show_exception(f"[bold red] # ERROR:  {command.name}: {repr(e)}", e)
            return False

        return True


@inject
class ActionRegistry:
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
        self.actions.append(action)

    def remove(self, name: str):
        self.actions = [a for a in self.actions if name == '' or a.name != name]

    def process_line(self, line: str):
        act: Action
        for act in sorted(self.actions, key=lambda x: x.priority, reverse=True):
            match = act.compiled_re.search(line)
            if match:
                self.initiate_callback(act, match)

    def initiate_callback(self, action: Action, match: Match):
        g = match.groups()

        # perform type conversions
        if len(g) < action.expected_match_groups:
            msg = f"Incorrect # of match groups.  Expected {action.expected_match_groups}, got {g}"
            self.session.output(f"[bold red] # ERROR: {msg} {repr(action)}")

        args = []

        for arg_type, value in zip(action.parameter_types, match.groups()):
            if arg_type == Match:
                value = match
            elif callable(arg_type) and arg_type.__name__ != '_empty':
                # fancy type conversion
                value = arg_type(value)

            args.append(value)

        # call with the list of args
        action.callback(*args)
