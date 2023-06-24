from __future__ import annotations

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import Plugin, command


class AliasCommand(Plugin):
    @command(name="alias")
    def alias(self):
        """list, remove add aliases"""
        buf = "[bold white]Aliases:\n"
        for key in self.director.alias_manager.aliases.items():
            self.session.output(Pretty(key), actionable=False)
            buf += f"{key[0]}: {key[1]}\n"

        self.session.output(Panel(buf), actionable=False)
