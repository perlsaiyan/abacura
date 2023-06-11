import inspect
import os
import shlex
from importlib import import_module
from pathlib import Path
from typing import List, Dict


from rich.markup import escape
from serum import inject
from textual import log
from textual.app import App
from textual.widgets import TextLog

from abacura import Config
from abacura.mud import BaseSession
from abacura.plugins import Plugin


class CommandFunction:
    substitutes = {'question': '?', 'at': '@'}

    def __init__(self, plugin: Plugin, fn: callable):
        self.fn = fn
        self.plugin = plugin

        # if cmd_name == "" or cmd_name == "-h" or cmd_name == "--help":
        #     return self.get_help()

        self.name = self.substitutes.get(fn.command_name, fn.command_name)

    def __call__(self, context, cmd_str: str):
        submitted_arguments = shlex.split(cmd_str)

        submitted_options = [s.strip("-") for s in submitted_arguments if s.startswith("-")]
        submitted_arguments = [s for s in submitted_arguments if not s.startswith("-")]

        d = self.evaluate_options(submitted_options)
        if 'help' in d:
            return self.get_help()

        d.update(self.evaluate_arguments(submitted_arguments, cmd_str))
        d['context'] = context

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
        return [p for p in parameters if p.annotation != bool and p.name != "context"]

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
        self.inspect_plugin()

    def get_plugin_name(self) -> str:
        return self.plugin.__class__.__name__

    def do(self, line, context):
        self.plugin.do(line, context)

    def get_matching_commands(self, command: str) -> List[CommandFunction]:
        return [fn for fn in self.command_functions if fn.name.startswith(command) and self.plugin.plugin_enabled]

    def inspect_plugin(self):
        for name, member in inspect.getmembers(self.plugin):
            if not callable(member):
                continue

            if hasattr(member, "command_name"):
                log(f"Appending command function '{member.command_name}'")
                self.command_functions.append(CommandFunction(self.plugin, member))

            # if hasattr(fn, 'scanner'):
            #     self.scanner_functions.append(fn)
            #
            # if hasattr(fn, 'ticker_interval'):
            #     self.ticker_functions.append(TickerFunction(fn))
            #
            # if hasattr(fn, 'listener_event'):
            #     self.listener_functions.append(fn)
            #     if getattr(fn, 'listener_while_disabled', False):
            #         listener = fn
            #     else:
            #         listener = partial(self.dispatch, fn)
            #     self.dispatcher.add_listener(fn.listener_event, listener)
            #
            # if hasattr(fn, "action_re"):
            #     self.action_functions.append(ActionFunction(fn))


@inject
class PluginManager(Plugin):
    """Manages and loads all plugins, command functions, etc"""
    config: Config
    sessions: dict
    session: BaseSession
    app: App
    tl: TextLog

    def __init__(self):
        super().__init__()
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_handlers: List[PluginHandler] = []

        self.load_plugins()

    def handle_command_functions(self, line: str) -> bool:
        s = line.lstrip("@").rstrip("\n").split(" ")
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
                self.output(f"[orange][italic]> {escape(error_msg)}", markup=True, highlight=True)
                return False

        fn: CommandFunction = fns[0]
        try:
            context = {
                "app": self.app,
                "manager": self
            }
            self.output(f"[green][italic]> {escape(line)}", markup=True, highlight=True)
            fn(context, submitted_args)
        except AttributeError as e:
            self.session.show_exception(f"[bold red] # ERROR: {fn.name}: {repr(e)}", e)
            self.output(f"[gray][italic]> {escape(fn.get_help())}", markup=True, highlight=True)
            return False

        except (ValueError, NameError) as e:
            self.session.show_exception(f"[bold red] # ERROR:  {fn.name}: {repr(e)}", e)
            return False

        return True

    def handle_command(self, line: str) -> bool:
        """Handles command parsing, returns True if command handled
        so we can pass the command along to something else"""

        cmd = line.split()[0]
        cmd = cmd[1:]

        context = {
            "app": self.app,
            "manager": self
        }

        for p in self.plugin_handlers:
            # call do method
            if p.plugin.get_name() == cmd and p.plugin.plugin_enabled and getattr(p, "do"):
                try:
                    self.output(f"[green][italic]> {escape(line)}", markup=True, highlight=True)
                    p.do(line, context)

                except Exception as e:
                    self.session.show_exception(
                        f"[bold red] # ERROR: {p.__class__} {p.get_plugin_name()}: {repr(e)}", e
                        )
                return True

        return self.handle_command_functions(line)

    def output(self, msg, markup: bool = False, highlight: bool = False) -> None:
        self.tl.markup = markup
        self.tl.markup = highlight
        self.tl.write(msg)

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
                self.output(f"[bold red]# ERROR LOADING PLUGIN {package} (from {pf}): {repr(e)}",
                            markup=True, highlight=True)
                continue

            # Look for plugins subclasses within the module we just loaded and create a PluginHandler for each
            for name, c in inspect.getmembers(module, inspect.isclass):
                if c.__module__ == module.__name__ and inspect.isclass(c) and issubclass(c, Plugin):
                    plugin_instance: Plugin = c()
                    plugin_name = plugin_instance.get_name()
                    log(f"Adding plugin {name}.{plugin_name}")

                    self.plugins[plugin_name] = plugin_instance

                    handler = PluginHandler(plugin_instance)
                    self.plugin_handlers.append(handler)
