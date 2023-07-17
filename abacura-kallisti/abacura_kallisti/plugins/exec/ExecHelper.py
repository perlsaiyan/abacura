import ast
import uuid

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import command
from abacura_kallisti.plugins import LOKPlugin


class ExecHelper(LOKPlugin):
    """Run an async script"""

    def __init__(self):
        super().__init__()
        self.exec_locals = {}

    def add_response(self, pattern: str, message: str, flags: int = 0):
        name = str(uuid.uuid4())

        def do_response():
            self.send(message)
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
                            "send": self.send,
                            "input": self.session.player_input,
                            "world": self.world,
                            "msdp": self.msdp,
                            "pc": self.pc,
                            "cq": self.cq,
                            "locations": self.locations,
                            "room": self.room,
                            "history": self.output_history
                            }

            self.session.output(f"# Running script {filename}", actionable=False)

            source_code = open(filename, "r").read()
            ast.parse(source_code)

            source = open(filename, "r").read()
            ast.parse(source)

            result = exec(source_code, exec_globals, self.exec_locals)

            if result is not None:
                pretty = Pretty(result, max_length=20, max_depth=4)
                panel = Panel(pretty)
                self.session.output(panel)

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False

    @command(name="#")
    def exec_python(self, text: str, reset_locals: bool = False):
        """Execute python code and display results"""

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            exec_globals = {"session": self.session, "plugins": self.session.plugin_loader.plugins,
                            "output": self.output, "cq": self.cq,
                            "world": self.world, "msdp": self.msdp, "locations": self.locations,
                            "pc": self.pc, "room": self.room, "history": self.output_history}

            compiled = compile(text.strip(), '<string>', 'eval')
            result = eval(compiled, exec_globals, self.exec_locals)

            if result is not None:
                pretty = Pretty(result, max_length=20, max_depth=4)
                panel = Panel(pretty)
                self.session.output(panel)

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False
