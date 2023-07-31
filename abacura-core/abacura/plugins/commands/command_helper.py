import inspect
import re

from abacura.plugins import Plugin, command
from abacura.plugins.commands import Command
from abacura.utils.renderables import AbacuraPanel, tabulate, box, Group, Text, OutputColors


class CommandHelper(Plugin):
    """Display help for a command and evaluate a string"""

    def __init__(self):
        super().__init__()

    def show_command_help(self, cmd: Command):
        help_text = [""]

        doc_lines = []

        parameter_doc = {}
        fn_doc = getattr(cmd.callback, '__doc__') or ''
        re_param = re.compile(r".*:param (\w+): (.*)")
        for line in fn_doc.split("\n"):
            if m := re_param.match(line):
                name, description = m.groups()
                parameter_doc[name] = description
            elif len(line.strip(" \n")):
                doc_lines.append(line.strip())

        parameters = cmd.get_parameters()
        parameter_names = []
        parameter_rows = []
        for parameter in parameters:
            if parameter.default is inspect.Parameter.empty:
                parameter_names.append(parameter.name)
            else:
                parameter_names.append(f"[{parameter.name}]")

            if parameter.name in parameter_doc:
                pd = Text(f"({str(parameter.default)})")
                if parameter.default is inspect.Parameter.empty:
                    pd = ""
                elif parameter.default in (None, '', 0):
                    pd = "(optional)"

                parameter_rows.append((parameter.name, pd, parameter_doc.get(parameter.name, "")))

        if len(doc_lines):
            help_text.append(Text(" Purpose:\n", style=OutputColors.section))
            for line in doc_lines:
                help_text.append(Text("   " + line))
            help_text.append(Text(" "))
            # help_text.append(Text("\n".join(doc_lines) + "\n   "))

        help_text.append(Text(" Usage:\n", style=OutputColors.section))
        help_text.append(Text(f"   #{cmd.name} {' '.join(parameter_names)}"))

        g = Group(*[t for t in help_text])

        if len(parameter_rows):
            tbl = tabulate(parameter_rows, headers=["Arguments"], box=box.SIMPLE,
                           header_style=OutputColors.section)
            g.renderables.append(tbl)

        option_rows = []
        for name, p in cmd.get_options().items():
            if p.annotation in (bool, 'bool'):
                oname = f"--{name.lstrip('_')}"
                option_rows.append((oname, "", parameter_doc.get(name, '')))
            else:
                ptype = getattr(p.annotation, '__name__', p.annotation)
                oname = f"--{name.lstrip('_') + '=<' + ptype + '>'}"
                odefault = f"({str(p.default)})"
                if p.default is inspect.Parameter.empty:
                    odefault = ""
                elif p.default in (None, '', 0):
                    odefault = "(optional)"
                option_rows.append((oname, odefault, parameter_doc.get(name, '')))

        if len(option_rows):
            tbl = tabulate(sorted(option_rows),
                           headers=["Options"],
                           box=box.SIMPLE_HEAD,
                           header_style=OutputColors.section)
            g.renderables.append(tbl)

        self.output(AbacuraPanel(g, title=f"#{cmd.name} command"))

    @command(name="help", hide=True)
    def list_commands(self, name: str = '', hidden: bool = False):
        """
        Show available commands

        :param name: Show details about a specific command
        :param hidden: Show hidden commands
        """

        if isinstance(name, Command):
            self.show_command_help(name)
            return

        commands: list[Command] = list(self.director.command_manager.commands.values())

        if name != '':
            commands = [c for c in commands if c.name.startswith(name.lower())]
            if len(commands) > 0:
                self.show_command_help(commands[0])
                return
            else:
                self.session.show_error(f"Unknown command '{name}'")
                return

        commands = [c for c in self.director.command_manager.commands.values() if c.hide_help == hidden]
        rows = []

        for c in sorted(commands, key=lambda c: c.name):
            rows.append((c.name, c.get_description()))
            # help_text.append(f"  {c.name:14s} : {c.get_description()}")

        tbl = tabulate(rows, headers=["Command", "Description"], box=box.MINIMAL,
                       # title="Usage: #command <arguments>",
                       caption="Use '#<command> -?' to get help on a specific <command>")
        self.session.output(AbacuraPanel(tbl, title="Available Commands"))

    @command(name="?")
    def help_question(self):
        """Display list of commands"""
        self.list_commands()

    @command(hide=True)
    def repeat(self, n: int, text: str):
        """
        Repeat a command multiple times

        :param n: Number of times to repeat
        :param text: Text to send
        """
        if n <= 0:
            return

        # Note that "text" will contain the full command text including n, by convention
        m = re.match(r"(\d+)(.*)", text)
        if m:
            cmd = m.groups()[1]

            def do_repeat():
                self.session.player_input(cmd.strip())

            self.add_ticker(0.1, do_repeat, repeats=n, name="_repeat")

    @command(hide=True)
    def error(self, error_str, _warning: bool = False):
        title = "Ooops!"
        n = 1 / 0
        if _warning:
            self.session.show_warning(f"{error_str}", title=title)
        else:
            self.session.show_error(f"{error_str}", title=title)
