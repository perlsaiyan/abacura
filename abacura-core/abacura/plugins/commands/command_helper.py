from abacura.plugins import Plugin, command
import re


class CommandHelper(Plugin):
    """Display help for a command and evaluate a string"""

    def __init__(self):
        super().__init__()

    @command(hide=True)
    def help(self, hidden: bool = False):
        """Show available commands"""
        help_text = ["Plugin Commands", "\nUsage: @command <arguments>", "\nAvailable Commands: "]

        commands = [c for c in self.director.command_manager.commands.values() if c.hide_help == hidden]

        for c in sorted(commands, key=lambda c: c.name):
            help_text.append(f"  {c.name:14s} : {c.get_description()}")

        help_text.append("")
        self.session.output("\n".join(help_text))

    @command(name="?")
    def help_question(self):
        """Display list of commands"""
        self.help()

    @command(hide=True)
    def repeat(self, n: int, text: str):

        if n <= 0:
            return

        m = re.match(r"(\d+)(.*)", text)
        if m:
            cmd = m.groups()[1]

            def do_repeat():
                self.session.player_input(cmd.strip())

            self.add_ticker(0.1, do_repeat, repeats=n, name="_repeat")
