from typing import Optional

from abacura.plugins import Plugin, command
from abacura.utils.pycharm import PycharmDebugger


class PycharmDebug(Plugin):
    """Connect to the remote pycharm debugger"""

    def __init__(self):
        super().__init__()
        self.debugger: Optional[PycharmDebugger] = None

    @command(hide=True)
    def pycharm_debug(self, host: str = "localhost", port: int = 12345):
        """
        Connect to the remote pycharm debugger

        :param host: Host running pycharm debugger
        :param port: port of the debugger
        """
        self.debugger = PycharmDebugger()
        try:
            self.output(f"Connecting to {host}:{port}")
            self.debugger.connect(host, port)
        except ConnectionRefusedError:
            self.output(f"Connection refused by pycharm debugger {host}:{port}")
