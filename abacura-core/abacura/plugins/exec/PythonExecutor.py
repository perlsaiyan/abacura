import ast
import uuid
from typing import Dict, Callable

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import command, Plugin
from abacura.plugins.events import event, AbacuraMessage


class PythonExecutor(Plugin):
    """Run an async script"""

    def __init__(self):
        super().__init__()
        self.global_providers: Dict[str, Callable] = {"core": self.provide_core_globals}
        self.exec_locals = {}

    def provide_core_globals(self) -> Dict:
        return {"session": self.session,
                "plugins": self.session.plugin_loader.plugins,
                "respond": self.add_response,
                "action": self.add_action,
                "ticker": self.add_ticker,
                "output": self.output,
                "send": self.send,
                "input": self.session.player_input,
                "history": self.output_history
                }

    def get_globals(self) -> Dict:
        _globals = {}
        for provider in self.global_providers.values():
            _globals.update(provider())
        return _globals

    @event("core.exec.globals")
    def add_globals_provider(self, message: AbacuraMessage):
        if isinstance(message.value, dict):
            self.global_providers.update(message.value)

    def add_response(self, pattern: str, message: str, flags: int = 0):
        name = str(uuid.uuid4())

        def do_response():
            self.send(message)
            self.remove_action(name)
        self.add_action(pattern, do_response, flags=flags, name=name)

    @command
    def run(self, filename: str, reset_locals: bool = False):
        """
        Execute python code and display results

        :param filename: The filename containing the script to execute
        :param reset_locals: Reset local variables before running the script
        """

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            self.session.output(f"# Running script {filename}", actionable=False)

            source_code = open(filename, "r").read()
            ast.parse(source_code)

            source = open(filename, "r").read()
            ast.parse(source)

            result = exec(source_code, self.get_globals(), self.exec_locals)

            if result is not None:
                pretty = Pretty(result, max_length=20, max_depth=4)
                panel = Panel(pretty)
                self.session.output(panel)

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False

    @command(name="#")
    def exec_python(self, text: str, reset_locals: bool = False):
        """
        Execute python code and display results

        :param text: The python code to run
        :param reset_locals: Reset local variables that are saved between exec calls
        """

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            if text.strip().startswith("def "):
                result = exec(text, self.get_globals(), self.exec_locals)
                return

            # compile(text.strip(), '<string>', 'eval')
            # result = eval(compiled, self.get_globals(), self.exec_locals)

            exec("__result = " + text, self.get_globals(), self.exec_locals)
            result = self.exec_locals.get('__result', None)

            if result is not None:
                pretty = Pretty(result, max_length=100, max_depth=4)
                panel = Panel(pretty)
                self.session.output(panel)

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex, show_tb=False)
            return False
