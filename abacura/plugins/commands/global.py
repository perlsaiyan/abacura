"""Temporary module with 'global' commands

Need until Mard's PluginManager is ready
"""

import sys

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import Plugin, command, action, ticker


class PluginDemo(Plugin):
    """Sample plugin to knock around"""
    def __init__(self):
        super().__init__()
        self.exec_locals = {}

    @command
    def foo(self) -> None:
        self.manager.output(f"{sys.path}")
        self.manager.output(f"{self.app.sessions}", markup=True)
        self.manager.output(
            f"MSDP HEALTH: [bold red]🛜 [bold green]🛜  {self.manager}", markup=True)

    @ticker(15)
    def test_ticker(self):
        self.session.output("TICK!!")

    @action("Ptam")
    def ptam(self):
        self.session.output("PTAM!!")

    @action("Ptam (.*)")
    def ptam2(self, s: str):
        self.session.output(f"PTAM!! [{s}]")

class PluginCommandHelper(Plugin):
    """Display help for a command and evaluate a string"""

    @command()
    def help(self):
        help_text = ["Plugin Commands", "\nUsage: @command <arguments>", "\nAvailable Commands: "]

        commands = []
        for h in self.manager.plugin_handlers:
            commands += [c for c in h.command_functions if c.name != 'help']

        for c in sorted(commands, key=lambda c: c.name):
            doc = getattr(c.fn, '__doc__', None)
            doc = "" if doc is None else ": " + doc
            help_text.append(f"  {c.name:10s} {doc}")

        help_text.append("")
        self.session.output("\n".join(help_text))

    @command()
    def at(self, text: str, reset_locals: bool = False):
        """Execute python code and display results"""

        try:
            if self.exec_locals is None or reset_locals:
                self.exec_locals = {}

            exec_globals = {"app": self.app, "manager": self.manager, "session": self.session,
                            'mean': lambda x: sum(x) / len(x)}

            if text.strip().startswith("def "):
                result = exec(text, exec_globals, self.exec_locals)
            else:
                exec("__result = " + text, exec_globals, self.exec_locals)
                result = self.exec_locals.get('__result', None)

            if result is not None:
                # TODO: Pretty print
                self.session.output(str(result))

        except Exception as ex:
            self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
            return False


class PluginData(Plugin):
    @command
    def plugin(self) -> None:
        """Get information about plugins"""

        self.session.output("Current registered global plugins:")

        for plugin_name, plugin in self.manager.plugins.items():
            indicator = '[bold green]✓' if plugin.plugin_enabled else '[bold red]x'
            self.session.output(
                f"{indicator} [white]{plugin.get_name()}" +
                f" - {plugin.get_help()}", markup=True)


class PluginSession(Plugin):
    """Session specific commands"""

    @command(name="echo")
    def echo(self, text: str):
        # TODO: I think we have showme and echo backwards
        """Send text to screen without triggering actions"""
        self.session.output(text)

    @command
    def showme(self, text: str) -> None:
        # TODO: I think we have showme and echo backwards
        """Send text to screen as if it came from the socket, triggers actions"""
        self.manager.output(text, markup=True)

    @command
    def connect(self, name: str, host: str = '', port: int = 0) -> None:
        """@connect <name> <host> <port> to connect a game session"""

        conf = self.app.config

        if name in self.app.sessions:
            self.session.output("[bold red]# SESSION ALREADY EXISTS", markup=True)
            return

        if name in conf.config and not host and not port:
            self.app.create_session(name)
            self.app.run_worker(self.app.sessions[name].telnet_client(
                conf.config[name]["host"], int(conf.config[name]["port"])))
        elif not host and not port:
            self.manager.output(
                " [bold red]#connect <session name> <host> <port>", markup=True, highlight=True)
        else:
            self.app.create_session(name)
            self.app.run_worker(self.app.sessions[name].telnet_client(host, port))

    @command
    def session(self, name: str = "") -> None:
        """@session <name>: Get information about sessions or swap to session <name>"""
        if not name:
            cur = self.app.session
            buf = "[bold red]# Current Sessions:\n"
            for ses in self.app.sessions:
                if ses == cur:
                    buf += "[bold green]>[white]"
                else:
                    buf += " [white]"
                session = self.app.sessions[ses]

                if ses == "null":
                    buf += f"{session.name}: Main Session\n"
                else:
                    if session.connected:
                        buf += f"{session.name}: {session.host} {session.port}\n"
                    else:
                        buf += f"{session.name}: {session.host} {session.port} [red]\\[disconnected]\n"

            self.manager.output(buf, markup=True, highlight=True)
        else:
            if name in self.app.sessions:
                self.app.set_session(name)
            else:        
                self.session.output(
                    f"[bold red]# INVALID SESSION {name}", markup=True)

    @command
    def msdp(self, variable: str = '') -> None:
        """Dump MSDP values for debugging"""
        msdp = self.app.sessions[self.app.session].options[69]

        if not variable:
            panel = Panel(Pretty(msdp.values), highlight=True)
            self.manager.output(panel, highlight=True)
        else:
            panel = Panel(Pretty(msdp.values.get(variable, None)), highlight=True)
            self.manager.output(panel, highlight=True)


class PluginMeta(Plugin):
    @command
    def meta(self) -> None:
        """Hyperlink demo"""
        self.manager.output("Meta info blah blah")
        self.manager.output("Obtained from https://kallisti.nonserviam.net/hero-calc/Pif")
