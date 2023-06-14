from __future__ import annotations

import re
import inspect
import os
import shlex
from importlib import import_module
from pathlib import Path
from typing import List, Dict, TYPE_CHECKING, Callable, Match
from datetime import datetime, timedelta
import heapq

from rich.markup import escape
from serum import inject, Context
from textual import log
from textual.app import App
from textual.widgets import TextLog

from abacura import Config
from abacura.plugins import Plugin

if TYPE_CHECKING:
    from abacura.mud.session import Session


class Action:
    def __init__(self, pattern: str, callback: Callable, source: object,
                 flags: int = 0, name: str = '', color: bool = False):
        self.pattern = pattern
        self.callback = callback
        self.flags = flags
        self.compiled_re = re.compile(pattern, flags)
        self.name = name
        self.color = color
        self.source = source

        self.parameters = list(inspect.signature(callback).parameters.values())
        self.parameter_types = [p.annotation for p in self.parameters]
        self.expected_match_groups = len([t for t in self.parameter_types if t != Match])

        valid_type_annotations = [str, int, float, inspect._empty, Match]
        invalid_types = [t for t in self.parameter_types if t not in valid_type_annotations]

        if invalid_types:
            raise TypeError(f"Invalid action parameter type: {callback}({invalid_types})")


@inject
class ActionRegistry:
    session: Session

    def __init__(self):
        self.actions = []

    def register_actions(self, obj: object):
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "action_pattern"):
                act = Action(pattern=getattr(member, "action_pattern"), callback=member, source=obj,
                             flags=getattr(member, "action_flags"), color=getattr(member, "action_color"))
                self.add(act)

    def unregister_actions(self, obj: object):
        self.actions = [a for a in self.actions if a.source != obj]

    def add(self, action: Action):
        self.actions.append(action)

    def remove(self, name: str):
        self.actions = [a for a in self.actions if name == '' or a.name != name]

    def process_line(self, line: str):
        act: Action
        for act in self.actions:
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


class TickerFunction:
    def __init__(self, fn: callable):
        self.fn = fn
        self.interval: float = getattr(fn, 'ticker_interval', 0.250)
        self.last_tick = datetime.utcnow()
        self.next_tick = self.last_tick + timedelta(seconds=self.interval)

    def __call__(self, enabled: bool = True) -> datetime:
        now = datetime.utcnow()
        if self.next_tick <= now:
            # try to keep ticks aligned , so use the last target (next_tick) as the basis for adding the interval
            self.next_tick = max(now, self.next_tick + timedelta(seconds=self.interval))
            self.last_tick = now
            if enabled:
                self.fn()

        return self.next_tick


class CommandFunction:
    def __init__(self, plugin: Plugin, fn: callable):
        self.fn = fn
        self.plugin = plugin
        self.name = self.fn.command_name

    def __call__(self, cmd_str: str):
        submitted_arguments = shlex.split(cmd_str)

        submitted_options = [s.strip("-") for s in submitted_arguments if s.startswith("-")]
        submitted_arguments = [s for s in submitted_arguments if not s.startswith("-")]

        d = self.evaluate_options(submitted_options)
        if 'help' in d:
            return self.get_help()

        d.update(self.evaluate_arguments(submitted_arguments, cmd_str))

        return self.fn(**d)

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

            evaluated_args[parameter.name] = self.plugin.evaluate_command_argument(parameter, value)

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
        parameters = inspect.signature(self.fn).parameters.values()
        return [p for p in parameters if p.annotation != bool]

    def get_boolean_options(self):
        parameters = inspect.signature(self.fn).parameters.values()
        return {p.name: p.default for p in parameters if p.annotation == bool}

    def get_help(self):
        help_text = []

        doc = getattr(self.fn, '__doc__', None)

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


class PluginHandler:
    def __init__(self, plugin: Plugin):
        super().__init__()
        self.plugin = plugin
        self.command_functions: List[CommandFunction] = []
        self.ticker_functions: List[TickerFunction] = []

        self.inspect_plugin()

    def get_plugin_name(self) -> str:
        return self.plugin.__class__.__name__

    def do(self, line, context):
        self.plugin.do(line, context)

    def tick(self):
        next_ticks = [fn(self.plugin.plugin_enabled) for fn in self.ticker_functions]
        if len(next_ticks) == 0:
            return None

        return min(next_ticks)

    def get_matching_commands(self, command: str) -> List[CommandFunction]:
        return [fn for fn in self.command_functions if fn.name.startswith(command) and self.plugin.plugin_enabled]

    def inspect_plugin(self):
        for name, member in inspect.getmembers(self.plugin):
            if not callable(member):
                continue

            if hasattr(member, "command_name"):
                log(f"Appending command function '{member.command_name}'")
                self.command_functions.append(CommandFunction(self.plugin, member))

            # if hasattr(member, 'ticker_interval'):
            #     self.ticker_functions.append(TickerFunction(member))

            if hasattr(member, "alias_name"):
                log(f"Appending alias function '{member.alias_name}")

            # if hasattr(fn, 'scanner'):
            #     self.scanner_functions.append(fn)
            #
            # if hasattr(fn, 'listener_event'):
            #     self.listener_functions.append(fn)
            #     if getattr(fn, 'listener_while_disabled', False):
            #         listener = fn
            #     else:
            #         listener = partial(self.dispatch, fn)
            #     self.dispatcher.add_listener(fn.listener_event, listener)
            #


@inject
class PluginManager(Plugin):
    """Manages and loads all plugins, command functions, etc"""
    config: Config
    sessions: dict
    session: Session
    action_registry: ActionRegistry
    app: App
    tl: TextLog

    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_handlers: List[PluginHandler] = []
        self.ticker_heap = []

        self.load_plugins()

        for handler in self.plugin_handlers:
            next_tick = handler.tick()
            if next_tick:
                heapq.heappush(self.ticker_heap, (next_tick, handler))

    def execute_command(self, line: str) -> bool:
        # remove the @ from the command name
        if not len(line):
            return False

        # remove leading @
        s = line[1:].rstrip("\n").split(" ")
        submitted_command = s[0]
        submitted_args = "" if len(s) == 1 else " ".join(s[1:])

        if submitted_command == '':
            submitted_command = 'help'

        fns: List[callable] = []
        for handler in self.plugin_handlers:
            fns += handler.get_matching_commands(submitted_command)

        if len(fns) == 0:
            error_msg = f"Unknown Command {submitted_command}"
            self.output(f"[orange][italic]> {escape(error_msg)}", markup=True, highlight=True)
            return False

        if len(fns) > 1:
            # look for partial matches
            starts_fns = [fn for fn in fns if fn.name.lower().startswith(submitted_command.lower())]
            exact_matches = [fn for fn in fns if fn.name.lower() == submitted_command.lower()]
            if len(exact_matches) == 1:
                fns = exact_matches
            elif len(starts_fns) > 1:
                matches = ", ".join([fn.name for fn in starts_fns])
                error_msg = f"Ambiguous command '{submitted_command}' [{matches}]"
                self.session.output(f"[orange][italic]> {escape(error_msg)}", markup=True, highlight=True)
                return False

        fn: CommandFunction = fns[0]
        try:
            self.session.output(f"[green][italic]> {escape(line)}", markup=True, highlight=True)
            message = fn(submitted_args)
            if message:
                self.session.output(message)

        except AttributeError as e:
            self.session.show_exception(f"[bold red] # ERROR: {fn.name}: {repr(e)}", e)
            self.session.output(f"[gray][italic]> {escape(fn.get_help())}", markup=True, highlight=True)
            return False

        except (ValueError, NameError) as e:
            self.session.show_exception(f"[bold red] # ERROR:  {fn.name}: {repr(e)}", e)
            return False

        return True

    def process_tickers(self):
        dt: datetime = datetime.utcnow()
        while self.ticker_heap and self.ticker_heap[0][0] <= dt:
            next_tick, handler = heapq.heappop(self.ticker_heap)
            next_tick = handler.tick()
            if next_tick:
                heapq.heappush(self.ticker_heap, (next_tick, handler))

    def load_plugins(self) -> None:
        """Load plugins"""
        framework_path = Path(os.path.realpath(__file__))
        plugin_path = framework_path.parent.parent

        plugin_files = []
        # plugin_files = [pf for pf in plugin_path.glob('plugins/commands/*.py') if not pf.name.startswith('_')]
        log.debug(f"Loading plugins from {plugin_path} from {__file__}")
        for dirpath, _, filenames in os.walk(plugin_path):
            for filename in [f for f in filenames if f.endswith(".py") and not f.startswith('_') and os.path.join(dirpath, f) != __file__]:
                log(f"Found plugin {os.path.join(dirpath,filename)}")
                plugin_files.append(Path(os.path.join(dirpath, filename)))

        # TODO: We may want to handle case where we are loading plugins a second time
        self.plugins = {}
        self.plugin_handlers = []
        
        # import each one of the modules corresponding to each plugin .py file
        for pf in plugin_files:
            log.debug(f"Loading file {pf}")
            package = str(pf.relative_to(plugin_path.parent.parent)).replace(os.sep, ".")
            package = package[:-3]  # strip .py
            package = package[8:]
            
            try:
                module = import_module(package)
            except Exception as e:
                self.session.output(f"[bold red]# ERROR LOADING PLUGIN {package} (from {pf}): {repr(e)}",
                                    markup=True, highlight=True)
                continue

            # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
            for name, c in inspect.getmembers(module, inspect.isclass):
                if c.__module__ == module.__name__ and inspect.isclass(c) and issubclass(c, Plugin):
                    with Context(app=self.app, manager=self, session=self.session,
                                 action_registry=self.action_registry):
                        plugin_instance: Plugin = c()

                    self.action_registry.register_actions(plugin_instance)

                    plugin_name = plugin_instance.get_name()
                    log(f"Adding plugin {name}.{plugin_name}")

                    self.plugins[plugin_name] = plugin_instance

                    handler = PluginHandler(plugin_instance)
                    self.plugin_handlers.append(handler)

                    # Look for listeners in the plugin
                    for member_name, member in inspect.getmembers(plugin_instance):
                        if not callable(member):
                            continue

                        if hasattr(member, 'event_name'):
                            log(f"Appending listener function '{member_name}'")
                            self.session.event_manager.listener(member.event_trigger, member)
