from __future__ import annotations

from abacura.plugins import Plugin, command
from rich.table import Table


class ScriptHelper(Plugin):

    def __init__(self):
        super().__init__()

    @command(name="scripts")
    def list_scripts(self):
        """Display list of scripts"""
        tbl = Table()
        tbl.add_column("Script Name")
        tbl.add_column("Script Function")
        tbl.add_column("Script Source")

        for s in self.scripts.get_scripts():
            tbl.add_row(s.name, str(s.script_fn), str(s.source))

        self.output(tbl)
