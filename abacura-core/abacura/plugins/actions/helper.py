from __future__ import annotations

from typing import TYPE_CHECKING, Callable
from rich.table import Table
from rich.markup import escape

from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPanel
from abacura.utils import ansi_escape

if TYPE_CHECKING:
    pass


class ActionCommand(Plugin):
    """Provides #ticker command"""
    def show_actions(self):
        rows = []
        for action in self.director.action_manager.actions.queue:
            callback_name = getattr(action.callback, "__qualname__", str(action.callback))
            source = action.source.__class__.__name__ if action.source else ""

            rows.append((repr(action.pattern), callback_name, action.priority, action.flags))

        tbl = tabulate(rows, headers=["Pattern", "Callback", "Priority", "Flags"],
                       caption=f" {len(rows)} actions registered")
        self.output(AbacuraPanel(tbl, title="Registered Actions"))

    @command
    def action(self):
        """
        View actions

        """
        self.show_actions()
