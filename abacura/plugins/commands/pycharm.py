import importlib

from abacura.plugins import Plugin, command


class PycharmDebug(Plugin):

    @command
    def pycharm_debug(self, context, host: str = "localhost", port=12345):
        session = context["manager"].session
        session.output("PTAM!!")

        try:
            module = importlib.import_module("pydevd_pycharm")
        except Exception as ex:
            session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False

        settrace = getattr(module, "settrace", None)

        if not settrace:
            session.output("Unable to load pycharm debug module")
            return False

        try:
            settrace(host, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
            session.output(f"Connected to pycharm debugger {host}:{port}")
        except ConnectionRefusedError:
            session.output(f"Connection refused by pycharm debugger {host}:{port}")
