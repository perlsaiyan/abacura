"""The Event plugin"""
from abacura.plugins import Plugin, command
from abacura.plugins.events import event, AbacuraMessage
from rich.table import Table


class EventPlugin(Plugin):
    """Commands and things """

    def __init__(self):
        super().__init__()
        self.dispatcher = self.session.dispatcher
        self.event_manager = self.session.director.event_manager

    @command(name="events")
    def eventscommand(self, detail: bool = False):
        """Show events"""
        tbl = Table(row_styles=["yellow4","sky_blue2"])
        tbl.add_column("Event Name")
        tbl.add_column("Count", justify="right")
        if detail:
            tbl.add_column("Handlers")

        for key in self.event_manager.events.keys():
            if detail:
                handlers = [f"{str(f.handler.__module__)}.{str(f.handler.__name__)}" for f in self.event_manager.events[key].queue]
                tbl.add_row(key, str(self.event_manager.events[key].qsize()), ", ".join(handlers))
            else:
                tbl.add_row(key, str(self.event_manager.events[key].qsize()))

        self.session.output(tbl, markup=True, highlight=True, actionable=False)

    @command(name="testevent")
    def eventsfire(self, trigger: str = "sample"):
        """Fires a test event to sample"""
        self.session.output(f"Sending test event to '{trigger}' dispatcher")
        self.dispatcher(AbacuraMessage("sample", "TEST OF EVENT FIRING"))

    @event("sample", priority=5)
    def sampleevent(self, message: AbacuraMessage):
        self.session.output(f"I just got an event, '{message.value}'")
