"""
Commands for dealing with textual/async workers
"""
from __future__ import annotations

from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from textual import log

from abacura.plugins import Plugin, command

class WorkersPlugin(Plugin):

    @command(name="workers")
    def workers(self, group: str=""):
        """Show all workers or for optional group"""
        
        if group == "":
            group = self.session.name

        if group == "global":
            group = ""
            table = Table(title="[cyan]Current Running Workers")
        else:
            table = Table(title=f"[cyan]Current Running Workers in Group '{group}'")
        table.add_column("Group", justify="right", style="bold white")
        table.add_column("Name", justify="left", style="bold white")
        table.add_column("Description", justify="left", style="bold white")
        
        for worker in filter(lambda x: group == "" or group == x.group, self.session.abacura.workers):
            table.add_row(worker.group, worker.name, worker.description)
        
        self.output(Panel(table), actionable=False, highlight=True)