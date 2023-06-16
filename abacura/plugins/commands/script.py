import uuid
import ast

from abacura.plugins import Plugin, command


class Script(Plugin):
    """Connect to the remote pycharm debugger"""

    def __init__(self):
        super().__init__()
        self.exec_locals = {}

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
                            "output": self.session.output,
                            "send": self.session.send,
                            "input": self.session.player_input
                            }

            self.session.output(f"# Running script {filename}", actionable=False)

            source = open(filename, "r").read()
            ast.parse(source)
            result = exec(source, exec_globals, self.exec_locals)

            if result is not None:
                self.session.output(str(result))

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False

    @command(name="@")
    def exec_python(self, text: str, reset_locals: bool = False):
        """Execute python code and display results"""

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            exec_globals = {"session": self.session,
                            'mean': lambda x: sum(x) / len(x)}

            if text.strip().startswith("def "):
                result = exec(text, exec_globals, self.exec_locals)
            else:
                exec("__result = " + text, exec_globals, self.exec_locals)
                result = self.exec_locals.get('__result', None)

            if result is not None:
                # TODO: Pretty print
                self.session.output(str(result))

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False
