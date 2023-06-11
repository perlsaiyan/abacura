"""Temporary module with 'global' commands

Need until Mard's PluginManager is ready
"""

import sys

from rich.markup import escape
from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import Plugin, command


class PluginDemo(Plugin):
    """Sample plugin to knock around"""
    name = "foo"
    plugin_enabled = True

    def do(self, line, context) -> None:
        manager = context["manager"].session.options[69].values["HEALTH"]
        app = context["app"]

        context["manager"].output(f"{sys.path}")
        context["manager"].output(f"{app.sessions}", markup=True)
        context["manager"].output(
            f"MSDP HEALTH: [bold red]🛜 [bold green]🛜  {manager}", markup=True)

    @command(name="echo")
    def echo(self, context, message: str, repeat: int = 1, foo: bool = False):
        session = context["manager"].session
        for _ in range(repeat):
            session.output(message)
        if foo:
            session.output("FOO!")

    @command()
    def help(self, context):
        help_text = ["Plugin Commands", "\nUsage: @command <arguments>", "\nAvailable Commands: "]

        manager = context["manager"]
        session = context["manager"].session

        commands = []
        for h in manager.plugin_handlers:
            commands += [c for c in h.command_functions if c.name != 'help']

        for c in sorted(commands, key=lambda c: c.name):
            doc = getattr(c.fn, '__doc__', None)
            doc = "" if doc is None else ": " + doc
            help_text.append("  %10s%s" % (c.name, doc))

        help_text.append("")
        session.output("\n".join(help_text))


class PluginShowme(Plugin):
    """Send text to screen as if it came from the socket, triggers actions"""
    name = "showme"

    def do(self, line, context) -> None:
        ses = context["app"].sessions[context["app"].session]
        data = line.split(' ', 1)
        ses.output(data[1], markup=True)


class PluginData(Plugin):
    """Get information about plugins"""
    name = "plugin"

    def do(self, line, context) -> None:
        ses = context["app"].sessions[context["app"].session]

        ses.output("Current registered global plugins:")

        for plugin_name in context["manager"].plugins:
            plugin = context["manager"].plugins[plugin_name]
            indicator = '[bold green]✓' if plugin.plugin_enabled else '[bold red]x'
            ses.output(f"{indicator} [white]{plugin.get_name()} - {plugin.get_help()}", markup=True)


# TODO clean this way up after we get injected config
class PluginConnect(Plugin):
    """@connect <name> <host> <port> to connect a game session"""
    name = "connect"

    def do(self, line, context) -> None:
        manager = context["manager"]
        ses = context["app"].sessions[context["app"].session]
        app = context["app"]
        conf = context["app"].config

        args = line.split()

        if len(args) == 2 and args[1] in conf:
            if args[1] in app.sessions:
                ses.output("[bold red]# SESSION ALREADY EXISTS", markup=True)
                return

            app.create_session(args[1])
            app.run_worker(app.sessions[args[1]].telnet_client(
                conf[args[1]]["host"], int(conf[args[1]]["port"])))
        elif len(args) < 4:
            manager.output(
                " [bold red]#connect <session name> <host> <port>", markup=True, highlight=True)
        else:
            if args[1] in app.sessions:
                ses.output("[bold red]# SESSION ALREADY EXISTS", markup=True)
                return
            app.create_session(args[1])
            app.run_worker(app.sessions[args[1]].telnet_client(
                args[2], int(args[3])))


class PluginSession(Plugin):
    """@session <name>: Get information about sessions or swap to session <name>"""
    name = "session"

    def do(self, line: str, context) -> None:
        manager = context["manager"]
        sessions = context["app"].sessions

        args = line.split()
        if len(args) == 1:
            cur = context["app"].session
            buf = "[bold red]# Current Sessions:\n"
            for ses in sessions:
                if ses == cur:
                    buf += "[bold green]>[white]"
                else:
                    buf += " [white]"
                session = sessions[ses]

                if ses == "null":
                    buf += f"{session.name}: Main Session\n"
                else:
                    if session.connected:
                        buf += f"{session.name}: {session.host} {session.port}\n"
                    else:
                        buf += f"{session.name}: {session.host} {session.port} [red]\\[disconnected]\n"

            manager.output(buf, markup=True, highlight=True)
        elif len(args) == 2:
            if args[1] in sessions:
                context["app"].set_session(args[1])
            else:
                manager.output(
                    f"[bold red]# INVALID SESSION {args[1]}", markup=True)
        else:
            manager.output("[bold red]@session <name>",
                           markup=True, highlight=True)


class PluginMSDP(Plugin):
    """Dump MSDP values for debugging"""
    name = "msdp"

    def do(self, line, context) -> None:
        msdp = context["app"].sessions[context["app"].session].options[69]
        manager = context["manager"]
        args = line.split()

        if len(args) == 1:
            panel = Panel(Pretty(msdp.values), highlight=True)
            manager.output(panel, highlight=True)
        elif len(args) == 2:
            panel = Panel(Pretty(msdp.values[args[1]]), highlight=True)
            manager.output(panel, highlight=True)
        else:
            manager.output("[bold red]# MSDP: too much args")


class PluginConfig(Plugin):
    """Show configuration information"""
    name = "config"

    def do(self, line, context) -> None:
        args = line.split()

        if len(args) == 1:
            if context["app"].session == "null":
                conf = escape(context["manager"].config.as_string())
            else:
                conf = escape(
                    context["manager"].config[context["app"].session].as_string())
        else:
            conf = escape(context["manager"].config[args[1]].as_string())

        panel = Panel(conf, highlight=True)
        tl = context["manager"].tl
        tl.markup = True
        tl.write(panel)
        tl.markup = False


class PluginMeta(Plugin):
    """Hyperlink demo"""
    name = "meta"

    def do(self, line, context) -> None:
        manager = context["manager"]
        manager.output("Meta info blah blah")
        manager.output(
            "Obtained from https://kallisti.nonserviam.net/hero-calc/Pif")
