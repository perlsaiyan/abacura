"""The Event plugin"""
from abacura.plugins import Plugin, command
from abacura.plugins.events import AbacuraMessage
from abacura.utils.tabulate import tabulate


class EventPlugin(Plugin):
    """Commands and things """

    def __init__(self):
        super().__init__()

    @command(name="events")
    def eventscommand(self, detail: bool = False):
        """
        Show event metrics and handlers

        :param detail: Show detailed method names
        """
        event_manager = self.session.director.event_manager

        rows = []
        for key, value in event_manager.events.items():
            row = {"Event Name": key,
                   "# Handlers": value.qsize(),
                   "# Events Processed": event_manager.event_counts[key]}
            if detail:
                row['Handlers'] = [f"{str(f.handler.__module__)}.{str(f.handler.__name__)}" for f in value.queue]

            rows.append(row)
        self.output(tabulate(rows), actionable=False)
        # self.session.output(tbl, markup=True, highlight=True, actionable=False)

    @command(name="dispatch")
    def dispatch_event(self, trigger: str, value: str = ""):
        """
        Dispatch an AbacuraMessage

        :param trigger: The event to trigger
        :param value: A value to send with the event
        """
        self.session.output(f"Sending {trigger} message: {value}")
        self.dispatch(AbacuraMessage(trigger, value))
