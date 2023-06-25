from __future__ import annotations

import inspect
import shlex
from typing import List, Dict, TYPE_CHECKING, Callable

from rich.markup import escape
from serum import inject
from textual import log

if TYPE_CHECKING:
    from abacura.mud.session import Session


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
        if parameter.annotation in [int, "int"]:
            return int(submitted_value)

        if parameter.annotation in [float, "float"]:
            return float(submitted_value)

        if parameter.annotation not in [str, "str"] and hasattr(parameter.annotation, "__name__"):
            parameter_class_name = parameter.annotation.__name__
            custom_evaluator_name = f"evaluate_argument_{parameter_class_name.lower()}"
            custom_evaluator = getattr(self.source, custom_evaluator_name, None)
            if custom_evaluator:
                return custom_evaluator(submitted_value)

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


@inject
class CommandManager:
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
            self.session.output(f"[orange1][italic]> {escape(error_msg)}", markup=True, highlight=True)
            return False
        else:
            matches = ", ".join([cmd.name for cmd in starts])
            error_msg = f"Ambiguous command '{submitted_command}' [{matches}]"
            self.session.output(f"[orange1][italic]> {escape(error_msg)}", markup=True, highlight=True)
            return False

        try:
            self.session.output(f"[green][italic]> {escape(command_line)}", markup=True, highlight=True)
            message = command.execute(submitted_args)
            if message:
                self.session.output(message)

        except AttributeError as e:
            self.session.show_exception(f"[bold red]# ERROR: {command.name}: {repr(e)}", e, show_tb=False)
            self.session.output(f"[gray][italic]> {escape(command.get_help())}", markup=True, highlight=True)
            return True

        except (ValueError, NameError) as e:
            self.session.show_exception(f"[bold red]# ERROR: {command.name}: {repr(e)}", e, show_tb=True)
            return True

        return True
