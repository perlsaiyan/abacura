import ast
import uuid

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import command
from abacura_kallisti.plugins import LOKPlugin
from .ScriptRunner import ScriptRunner
from typing import Optional
from textual.worker import Worker, WorkerState


class Script(LOKPlugin):
    """Connect to the remote pycharm debugger"""

    def __init__(self):
        super().__init__()
        self.exec_locals = {}
        self.fn = None
        self.runner: Optional[ScriptRunner] = None
        self.worker: Optional[Worker] = None

    def add_response(self, pattern: str, message: str, flags: int = 0):
        name = str(uuid.uuid4())

        def do_response():
            self.session.send(message)
            self.remove_action(name)
        self.add_action(pattern, do_response, flags=flags, name=name)

    @command
    def run(self, filename: str, reset_locals: bool = False):
        """Execute python code and display results"""

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            exec_globals = {"session": self.session,
                            "respond": self.add_response,
                            "action": self.add_action,
                            "ticker": self.add_ticker,
                            "output": self.output,
                            "send": self.session.send,
                            "input": self.session.player_input,
                            "world": self.world,
                            "msdp": self.msdp,
                            "pc": self.pc,
                            "locations": self.locations
                            }

            self.session.output(f"# Running script {filename}", actionable=False)

            source_code = open(filename, "r").read()
            ast.parse(source_code)

            # result = exec(source, exec_globals, self.exec_locals)
            # self.fn = self.exec_locals['_fn']
            self.runner = ScriptRunner(source_code, exec_globals, self.exec_locals)
            self.worker = self.session.abacura.run_worker(self.runner.run, group=self.session.name, name="fn test", exit_on_error=False)
            self.add_ticker(0.1, self.check_runner, repeats=-1, name="check_runner")
            #
            # if result is not None:
            #     pretty = Pretty(result, max_length=20, max_depth=4)
            #     panel = Panel(pretty)
            #     self.session.output(panel)

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False

    def check_runner(self):
        # self.output("check_runner")
        if self.worker and self.worker.state not in (WorkerState.RUNNING, WorkerState.PENDING):
            result = self.worker._error or self.worker.result
            self.output(f"Worker {self.worker.name}: {self.worker.state} - {result}")
            self.remove_ticker("check_runner")

    @command(name="#")
    def exec_python(self, text: str, reset_locals: bool = False):
        """Execute python code and display results"""

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            exec_globals = {"session": self.session, "plugins": self.session.plugin_loader.plugins,
                            "world": self.world, "msdp": self.msdp, "locations": self.locations,
                            "pc": self.pc}

            if text.strip().startswith("def "):
                result = exec(text, exec_globals, self.exec_locals)
            else:
                exec("__result = " + text, exec_globals, self.exec_locals)
                result = self.exec_locals.get('__result', None)

            if result is not None:
                pretty = Pretty(result, max_length=20, max_depth=4)
                panel = Panel(pretty)
                self.session.output(panel)

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False
