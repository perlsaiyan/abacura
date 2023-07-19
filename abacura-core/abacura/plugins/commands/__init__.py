from __future__ import annotations

import inspect
import shlex
from typing import List, Dict, TYPE_CHECKING, Callable, Tuple

from rich.markup import escape
from textual import log

if TYPE_CHECKING:
    from abacura.mud.session import Session


class CommandArgumentError(Exception):
    pass


class CommandError(Exception):
    pass


if TYPE_CHECKING:
    pass


class Command:
    def __init__(self, source: object, callback: Callable, name: str, hide_help: bool = False):
        self.callback = callback
        self.name = name
        self.source = source
        self.hide_help = hide_help

    def execute(self, command_arguments: str):
        submitted_arguments = shlex.split(command_arguments)

        submitted_options = [s.strip("-") for s in submitted_arguments if s.startswith("-")]

        d = self.evaluate_options(submitted_options)
        if 'help' in d:
            return self.get_help()

        submitted_arguments = [s for s in submitted_arguments if not s.startswith("-")]

        d.update(self.evaluate_arguments(submitted_arguments, command_arguments))

        return self.callback(**d)

    def evaluate_value(self, parameter: inspect.Parameter, submitted_value: str):
        if parameter.annotation in [int, "int"]:
            return int(submitted_value)

        if parameter.annotation in [float, "float"]:
            return float(submitted_value)

        if parameter.annotation not in [str, "str"] and hasattr(parameter.annotation, "__name__"):
            parameter_class_name = parameter.annotation.__name__
            custom_evaluator_name = f"evaluate_value_{parameter_class_name.lower()}"
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
                raise CommandArgumentError(f"Missing argument {parameter.name}")

            if len(submitted_arguments) > 0:
                if parameter.name.lower() == 'text':
                    value = cmd_str
                    submitted_arguments = []
                else:
                    value = submitted_arguments.pop(0)
            else:
                value = parameter.default

            evaluated_args[parameter.name] = self.evaluate_value(parameter, value)

        return evaluated_args

    def evaluate_options(self, submitted_options: List[str]) -> dict[str, any]:
        """evaluate options to command functions"""
        if len([so for so in submitted_options if so.lower() in ('h', 'help', '?')]):
            return {'help': True}

        if self.pass_full_command_text():
            return {}

        command_options = self.get_options()

        result = {name: p.default for name, p in command_options.items()}

        for so in submitted_options:
            so_name = so.split("=")[0] if so.find("=") else so

            matched_options = [k for k in command_options.keys() if k.lstrip("_").startswith(so_name.lower())]

            if len(matched_options) == 0:
                raise CommandArgumentError(f"Invalid option: {so_name}")

            if len(matched_options) > 1:
                raise CommandArgumentError(f"Ambiguous option: {so_name}")

            option_name = matched_options[0]

            if command_options[option_name].annotation in [bool, 'bool']:
                result[option_name] = True
                continue

            if so.find("=") < 0:
                raise CommandArgumentError(f"Please specify value for --{option_name.lstrip('_')}")

            submitted_value = so.split("=")[1]

            parameter = command_options[option_name]
            result[option_name] = self.evaluate_value(parameter, submitted_value)

        return result

    def pass_full_command_text(self) -> bool:
        return any([a for a in self.get_parameters() if a.name.lower() == 'text'])

    def get_parameters(self) -> List[inspect.Parameter]:
        parameters = inspect.signature(self.callback).parameters.values()
        return [p for p in parameters if p.annotation not in [bool, 'bool'] and not p.name.startswith("_")]

    def get_options(self) -> Dict[str, inspect.Parameter]:
        parameters = inspect.signature(self.callback).parameters.values()
        return {p.name: p for p in parameters if p.annotation in [bool, 'bool'] or p.name.startswith("_")}

    def get_description(self) -> str:
        doc = getattr(self.callback, '__doc__', None)
        if doc is None:
            return ""
        lines = [line.strip() for line in doc.split("\n") if len(line.strip())]
        return "" if len(lines) == 0 else lines[0]

    def get_help(self):
        help_text = []

        doc_lines = []

        parameter_doc = {}
        fn_doc = getattr(self.callback, '__doc__') or ''
        for line in fn_doc.split("\n"):
            if line.strip().startswith(":") and line.strip().find(" ") >= 0:
                s = line.lstrip(" :").split(" ")
                name = s[0]
                description = " ".join(s[1:])
                parameter_doc[name] = description
            elif len(line.strip(" \n")):
                doc_lines.append(line)

        parameters = self.get_parameters()
        parameter_names = []
        parameter_help = []
        for parameter in parameters:
            if parameter.default is inspect.Parameter.empty:
                parameter_names.append(parameter.name)
            else:
                parameter_names.append(f"[{parameter.name}]")
            if parameter.name in parameter_doc:
                parameter_help.append(f"    {parameter.name:30s} : {parameter_doc.get(parameter.name)}")

        if len(doc_lines):
            help_text.append("\n".join(doc_lines) + "\n")

        help_text.append(f"  Usage: {self.name} {' '.join(parameter_names)}")

        if len(parameter_help):
            help_text.append("")
            help_text.append("\n".join(parameter_help))

        option_help = []
        for name, p in self.get_options().items():
            if p.annotation in (bool, 'bool'):
                option_help.append(f"  --{name.lstrip('_'):30s} : {parameter_doc.get(name, '')}")
            else:
                ptype = getattr(p.annotation, '__name__', p.annotation)
                pname = f"{name.lstrip('_') + '=<' + ptype + '>'}"
                option_help.append(f"  --{pname:30s} : {parameter_doc.get(name, '')}")

        if len(option_help):
            help_text.append("\nOptions:\n")
            help_text += sorted(option_help)

        return "\n".join(help_text)


class CommandManager:

    def __init__(self, session: Session):
        self.commands: Dict[str, Command] = {}
        self.session = session

    def register_object(self, obj: object):
        # self.unregister_object(obj)  #  prevent duplicates
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "command_name"):
                name = member.command_name.lower()
                if name in self.commands and not member.command_override:
                    log(f"Skipping duplicate function '{member.command_name}' on {member}")
                    continue

                log(f"Adding command function '{member.command_name}'")
                self.commands[name] = Command(obj, member, member.command_name, member.command_hide)

    def unregister_object(self, obj: object):
        self.commands = {k: v for k, v in self.commands.items() if v.source != obj}

    def parse_command_line(self, command_line: str) -> Tuple[Command, str]:

        # remove leading @
        if command_line.startswith("##") and len(command_line) > 2:
            # TODO: This is a bugfix for the input splitter removing a space
            command_line = "## " + command_line[2:]

        s = command_line[1:].rstrip("\n").split(" ")
        command_str = s[0]
        argument_str = "" if len(s) == 1 else " ".join(s[1:])

        if command_str == '':
            command_str = 'help'

        # look for partial matches and exact matches
        starts = [cmd for cmd in self.commands.values() if cmd.name.lower().startswith(command_str.lower())]
        exact_matches = [cmd for cmd in self.commands.values() if cmd.name.lower() == command_str.lower()]

        if len(exact_matches) == 1:
            # use the exact match if we have 1
            command = exact_matches[0]
        elif len(starts) == 1:
            # use the partial match if there is only 1
            command = starts[0]
        elif len(starts) == 0:
            raise CommandError(f"Unknown command '{command_str}'")
        else:
            matches = ", ".join([cmd.name for cmd in starts])
            raise CommandError(escape(f"Ambiguous command '{command_str}' [{matches}]"))

        return command, argument_str

    def execute_command(self, command_line: str) -> bool:
        if not len(command_line):
            return False

        command: Command | None = None

        try:
            command, arg_str = self.parse_command_line(command_line)
            self.session.output(f"[green][italic]> {escape(command_line)}", markup=True, highlight=True)
            message = command.execute(arg_str)
            if message:
                self.session.output(message)

        except CommandArgumentError as exc:
            self.session.show_exception(f"[bold orange1]! {str(exc)}", exc, show_tb=False)
            if command is not None:
                self.session.output(f"[gray][italic]> {escape(command.get_help())}", markup=True, highlight=True)

        except CommandError as exc:
            self.session.show_exception(f"[bold orange1]! {str(exc)}", exc, show_tb=False)

        except Exception as exc:
            self.session.show_exception(str(exc), exc, show_tb=True)

        return True
