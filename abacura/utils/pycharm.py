import importlib


class PycharmDebugger:
    def __init__(self):
        self.module = importlib.import_module("pydevd_pycharm")
        self.settrace = getattr(self.module, "settrace", None)

    def connect(self, host: str, port: int):
        if not self.settrace:
            raise ValueError("settrace not found, install pydevd_pycharm module")

        self.settrace(host, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
