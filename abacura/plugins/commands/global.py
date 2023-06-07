from abacura.plugins import Plugin
from abacura.mud.session import Session
from tomlkit import dumps

from rich.markup import escape
from rich.pretty import Pretty
from rich.panel import Panel

class foo(Plugin):
    """Sample plugin to knock around"""
    name = "foo"
    plugin_enabled = True

    def do(self, line, context) -> None:
        s = context["manager"].config
        m = context["manager"].session.options[69].values["HEALTH"]
        app = context["app"]

        context["manager"].output(f"{app.sessions}", markup=True)
        context["manager"].output(f"MSDP HEALTH: {m}")
        
class plugindata(Plugin):
    """Get information about plugins"""
    name = "plugin"

    def do(self, line, context) -> None:
        buf = "Current registered global plugins:\n"
        for pn in context["manager"].plugins:
            p = context["manager"].plugins[pn]
            buf += f"{'[bold green]✓' if p.plugin_enabled else '[bold red]x' } [white]{p.get_name()} - {p.get_help()}\n"
        context["app"].handle_mud_data(context["app"].session, buf, markup=True, highlight=True)

class connect(Plugin):
    """@connect <name> <host> <port> to connect a game session"""
    name = "connect"

    def do(self, line, context) -> None:
        manager = context["manager"]
        app = context["app"]
        c = context["app"].config.config
        
        args = line.split()
        
        if len(args) == 2 and args[1] in c:
            if args[1] in app.sessions:
                    manager.tl.markup = True
                    manager.tl.write(f"[bold red]# SESSION ALREADY EXISTS")
                    manager.tl.markup = False
                    return
            app.create_session(args[1])
            app.run_worker(app.sessions[args[1]].telnet_client(app.handle_mud_data, c[args[1]]["host"], int(c[args[1]]["port"])))
        elif len(args) < 4:
            manager.output(f" [bold red]#connect <session name> <host> <port>", markup=True, highlight=True)
        else:
            if args[1] in app.sessions:
                manager.tl.markup = True
                manager.output(f"[bold red]# SESSION ALREADY EXISTS")
                manager.tl.markup = False
                return
            app.add_session(args[1])
            app.set_session(args[1])
            app.run_worker(app.sessions[args[1]].telnet_client(app.handle_mud_data, args[2], int(args[3])))

class session(Plugin):
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
                s = sessions[ses]

                if ses == "null":
                    buf += f"{s.name}: Main Session\n"
                else:
                    if s.connected:
                        buf += f"{s.name}: {s.host} {s.port}\n"
                    else:
                        buf += f"{s.name}: {s.host} {s.port} [red]\\[disconnected]\n"

            manager.output(buf, markup=True, highlight=True)
        elif len(args)  == 2:
            if args[1] in sessions:
                context["app"].set_session(args[1])
            else:
                manager.output(f"[bold red]# INVALID SESSION {args[1]}", markup=True)
        else:
            manager.output(f"[bold red]@session <name>", markup=True, highlight=True)

class config(Plugin):
    """Show configuration information"""
    name = "config"

    def do(self, line, context) -> None:
        args = line.split()

        if len(args) == 1:
            if context["app"].session == "null":
                c = escape(context["manager"].config.config.as_string())
            else:
                c = escape(context["manager"].config.config[context["app"].session].as_string())
        else:
            c = escape(context["manager"].config.config[args[1]].as_string())

        p = Panel(c, highlight = True)
        tl = context["app"].mudoutput(context["app"].session)
        tl.markup = True
        tl.write(p)
        tl.markup = False