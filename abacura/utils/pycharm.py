import importlib


class PycharmDebugger:
    def __init__(self):
        # self.module = importlib.import_module("pydevd_pycharm")
        # self.settrace = getattr(self.module, "settrace", None)
        pass

    def connect(self, host: str, port: int):
        import pydevd_pycharm
        pydevd_pycharm.settrace(host, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
