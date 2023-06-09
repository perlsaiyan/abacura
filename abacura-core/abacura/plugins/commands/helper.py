from __future__ import annotations

from abacura.plugins import Plugin, command


class CommandHelper(Plugin):
    """Display help for a command and evaluate a string"""

    def __init__(self):
        super().__init__()

    @command(hide=True)
    def help(self, hidden: bool=False):
        """Show available commands"""
        help_text = ["Plugin Commands", "\nUsage: @command <arguments>", "\nAvailable Commands: "]

        commands = [c for c in self.director.command_manager.commands if c.hide_help == hidden]

        for c in sorted(commands, key=lambda c: c.name):
            help_text.append(f"  {c.name:14s} : {c.get_description()}")

        help_text.append("")
        self.session.output("\n".join(help_text))

    @command(name="?")
    def help_question(self):
        """Display list of commands"""
        self.help()

