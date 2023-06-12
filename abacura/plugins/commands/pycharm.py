import importlib

from abacura.plugins import Plugin, command


class PycharmDebug(Plugin):
    """Connect to the remote pycharm debugger"""

    @command
    def pycharm_debug(self, host: str = "localhost", port=12345):
        try:
            module = importlib.import_module("pydevd_pycharm")
        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False

        settrace = getattr(module, "settrace", None)

        if not settrace:
            self.session.output("Unable to load pycharm debug module")
            return False

        try:
            settrace(host, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
            self.session.output(f"Connected to pycharm debugger {host}:{port}")
        except ConnectionRefusedError:
            self.session.output(f"Connection refused by pycharm debugger {host}:{port}")
