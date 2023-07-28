"""
Commands for dealing with textual/async workers
"""
from __future__ import annotations

from abacura.plugins import Plugin, command
from abacura.utils.renderables import tabulate, AbacuraPanel


class WorkersPlugin(Plugin):

    @command(name="workers")
    def workers(self, group: str = ""):
        """
        Show all workers or for optional group

        :param group: Show workers for this group only
        """
        
        title = "Running Workers"
        title += "" if group == "" else f" in Group '{group}'"

        rows = []
        for worker in filter(lambda x: group == "" or group == x.group, self.session.abacura.workers):
            rows.append((worker.group, worker.name, worker.description))

        tbl = tabulate(rows, headers=["Group", "Name", "Description"])
        self.output(AbacuraPanel(tbl, title=title), actionable=False, highlight=True)