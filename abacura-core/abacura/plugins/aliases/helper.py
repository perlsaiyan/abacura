from __future__ import annotations

from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from abacura.plugins import Plugin, command, CommandError


class AliasCommand(Plugin):
    @command(name="alias")
    def alias_cmd(self, alias: str = None, value: str = None, _add: bool = False, _delete: bool = False, _temporary: bool = False):
        """Add an alias that automatically replace text with a value in the inputbar"""

        if alias is None:
            tbl = Table(title="Alias Categories")
            tbl.add_column("Category Name")

            for c in self.director.alias_manager.get_categories():
                tbl.add_row(c)

            self.session.output(tbl)
            return

        s = alias.split(".")
        if len(s) > 2:
            raise CommandError('Alias should be of the format <category>.<name>')

        if _add and _delete:
            raise CommandError('Cannot specify both add and delete')

        category = s[0]

        if len(s) == 1:
            if _add or _delete:
                raise CommandError('Cannot add or delete category directly, use <category>.<name>')

            if category not in self.director.alias_manager.get_categories():
                raise CommandError(f'Unknown category {category}')

            aliases = []

            for a in self.director.alias_manager.get_category(category):
                aliases.append([a.cmd, a.value])

            tbl: Table = Table(title=f"{category}: aliases")
            tbl.add_column("Command")
            tbl.add_column("value")

            for a in aliases:
                tbl.add_row(*a)
            self.session.output(tbl)                
            return
        
        existing_alias = self.director.alias_manager.get_alias(alias)

        if _delete:
            if existing_alias is None:
                raise CommandError(f"Unknown alias {alias}")

            self.director.alias_manager.delete_alias(alias)
            self.session.output("Alias %s deleted" % alias)
            return

        if _add:
            if existing_alias is not None:
                raise CommandError(f"Alias %s already exists {alias}")

            if value is None:
                raise CommandError("The alias must have a definition")

            self.director.alias_manager.add_alias(alias, value, _temporary)
            self.session.output("Alias %s added for [%s]" % (alias, value))
            return


            