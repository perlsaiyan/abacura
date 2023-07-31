from abacura.utils.renderables import AbacuraPanel, tabulate

from abacura.plugins import Plugin, command, CommandError


class AliasCommand(Plugin):
    """Provides #alias command"""
    @command(name="alias")
    def alias_cmd(self, alias: str = None, value: str = None, _add: bool = False, _delete: bool = False, _temporary: bool = False):
        """
        Add an alias that automatically replace text with a value in the inputbar

        :param alias: category.name of the alias
        :param value: command to substitute
        :param _add: add an alias
        :param _delete: delete an alias
        :param _temporary: don't persist the alias
        """

        if alias is None:
            tbl = tabulate(self.director.alias_manager.get_categories(), headers=["Category Name"])
            self.output(AbacuraPanel(tbl, title="Alias Categories"))
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

            tbl = tabulate(aliases, headers=["Command", "Value"])
            self.output(AbacuraPanel(tbl, title=f"'{category}' aliases"))
            return
        
        existing_alias = self.director.alias_manager.get_alias(alias)

        if _delete:
            if existing_alias is None:
                raise CommandError(f"Unknown alias {alias}")

            self.director.alias_manager.delete_alias(alias)
            self.output("Alias %s deleted" % alias)
            return

        if _add:
            if existing_alias is not None:
                raise CommandError(f"Alias %s already exists {alias}")

            if value is None:
                raise CommandError("The alias must have a definition")

            self.director.alias_manager.add_alias(alias, value, _temporary)
            self.output("Alias %s added for [%s]" % (alias, value))
            return


            