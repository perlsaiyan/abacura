import re
import sys

from abacura.mud import OutputMessage
from abacura.plugins import Plugin, command, action


class PluginDemo(Plugin):
    """Sample plugin to knock around"""
    def __init__(self):
        super().__init__()

    @command
    def foo(self) -> None:
        self.session.output(f"{sys.path}")
        self.session.output(f"{self.session.app.sessions}", markup=True)
        self.session.output(
            f"MSDP HEALTH: [bold red]🛜 [bold green]🛜  {self.session}", markup=True)

    @action("Ptam", flags=re.IGNORECASE)
    def ptam(self):
        self.session.output("PTAM!!", actionable=False)

    @action("spoon", flags=re.IGNORECASE)
    def spoon(self, msg: OutputMessage):
        msg.gag = True

    @action("Ptam (.*)")
    def ptam2(self, s: str):
        self.session.output(f"PTAM!! [{s}]")
