import time

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPanel


class SessionHelper(Plugin):
    """Provides commands related to the session"""
    def __init__(self):
        super().__init__()
        if self.session.ring_buffer:
            self.add_ticker(1, self.session.ring_buffer.commit, name="ring-autocommit")

    """Session specific commands"""
    @command(name="echo")
    def echo(self, text: str):
        """
        Send text to the output window without triggering actions

        Use #showme to trigger actions

        :param text: The text to send to the output window
        """
        self.session.output(text, actionable=False)

    @command
    def showme(self, text: str) -> None:
        """
        Send text to the output window and trigger actions

        Use #echo to avoid triggering actions

        :param text: The text to send to the output window / trigger actions
        """
        self.session.output(text, markup=True)

    @command(name="msdp")
    def msdp_command(self, variable: str = '') -> None:
        """
        Dump MSDP values for debugging

        :param variable: The name of a variable to view, leave blank for all
        """
        if "REPORTABLE_VARIABLES" not in self.core_msdp.values:
            raise CommandError("MSDP not loaded")

        if not variable:
            panel = Panel(Pretty(self.core_msdp.values), highlight=True)
        else:
            panel = Panel(Pretty(self.core_msdp.values.get(variable, None)), highlight=True)
        self.session.output(panel, highlight=True, actionable=False)

    def ring_log_query(self, like: str = "", limit: int = 100, minutes_ago: int = 30,
                       hide_msdp: bool = False, show_commands: bool = False, grouped: bool = False):
        like = like[1:] if len(like) and like[0] == "^" else "%" + like
        like = like[:-1] + "\n" if len(like) and like[-1] == "$" else like + "%"
        # self.session.trace("like: %s" % like)

        ns_ago = int(minutes_ago) * 60 * 1000 * 1000 * 1000
        epoch_start = 0 if not minutes_ago else (time.time_ns() - ns_ago)

        clauses = ["stripped not like '%s%%'" % c for c in "@!&"] if hide_msdp else []

        exclude_commands = ['grep', 'log', 'trace']
        c = ["stripped not like '!&%s%%' and stripped not like '%%@%s%%'" % (cmd, cmd) for cmd in exclude_commands]
        clauses = clauses if show_commands else clauses + c

        clauses = [""] + clauses if len(clauses) else []
        exclude_clause = " and ".join(clauses)

        # self.session.trace("exclude: %s" % exclude_clause)

        # start_ns = time.time_ns()
        logs = self.session.ring_buffer.query(like, clause=exclude_clause, limit=limit,
                                              epoch_start=epoch_start, grouped=grouped)
        # end_ns = time.time_ns()
        # self.session.trace("ringlog: query took %d ms" % ((end_ns - start_ns)/1E6))

        search = like if not grouped else "distinct " + like

        s = f'Searching for {search}: ({len(logs)} matches)\n'

        for log_time, log_context, log_line in logs:
            s += f"\n{log_time:15} {log_context:>6} {log_line:90}"
        self.output(s, actionable=False, loggable=False)

    @command()
    def log(self, find: str = "%", limit: int = 40, minutes_ago: int = 30):
        """
        Search output log

        :param find: Search for text using sql % wildcard style
        :param limit: limit the number of log entries returned
        :param minutes_ago: limit how far back to search
        """
        if self.session.ring_buffer is None:
            raise CommandError("No output log ring buffer configured")
        self.ring_log_query(find, limit, hide_msdp=False, minutes_ago=minutes_ago)

    @command(name="workers")
    def workers(self, group: str = ""):
        """
        Show all workers or for optional group

        :param group: Show workers for this group only
        """

        title = "Running Workers"
        title += "" if group == "" else f" in Group '{group}'"

        rows = []
        for worker in filter(lambda x: group == "" or group == x.group, self.session.abacura.workers):
            rows.append((worker.group, worker.name, worker.description))

        tbl = tabulate(rows, headers=["Group", "Name", "Description"])
        self.output(AbacuraPanel(tbl, title=title), actionable=False, highlight=True)
