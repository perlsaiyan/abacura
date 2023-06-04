from abacura.plugins import Plugin

from rich.pretty import Pretty

class foo(Plugin):
    """Sample plugin to knock around"""
    name = "foo"
    plugin_enabled = True

    def do(self, line, context) -> None:
        context["manager"].output(f"[bold red]# FOO: {line} - {self.plugin_enabled}")

class plugindata(Plugin):
    """Get information about plugins"""
    name = "plugin"

    def do(self, line, context) -> None:
        buf = "Current registered global plugins:\n"
        for pn in context["manager"].plugins:
            p = context["manager"].plugins[pn]
            buf += f"{'[bold green]✓' if p.plugin_enabled else '[bold red]x' } [white]{p.get_name()} - {p.get_help()}\n"
        context["app"].handle_mud_data(context["app"].session, buf)

class connect(Plugin):
    """@connect <name> <host> <port> to connect a game session"""
    name = "connect"

    def do(self, line, context) -> None:
        manager = context["manager"]
        app = context["app"]

        args = line.split()
        if len(args) < 4:
            manager.output(f" [bold red]#connect <session name> <host> <port>")
        else:
            app.add_session(args[1])
            app.set_session(args[1])
            app.run_worker(app.sessions[args[1]].telnet_client(app.handle_mud_data, args[2], int(args[3])))

class session(Plugin):
    """Get information about sessions"""
    name = "session"

    def do(self, line, context) -> None:
        manager = context["manager"]
        sessions = context["app"].sessions
        cur = context["app"].session
        buf = "[bold red]# Current Sessions:\n"
        for ses in sessions:
            if ses == cur:
                buf += "[bold green]>[white]"
            else:
                buf += " [white]"
            s = sessions[ses]

            if ses == "null":
                buf += f"{s.name}: Main Session\n"
            else:
                buf += f"{s.name}: {s.host} {s.port}\n"
        
        manager.output(buf)