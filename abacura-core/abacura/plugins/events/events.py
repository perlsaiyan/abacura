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
    def eventscommand(self):
        """Show events"""
        tbl = Table()
        tbl.add_column("Event Name")
        tbl.add_column("# Handlers", justify="right")
        for key in self.event_manager.events.keys():
            tbl.add_row(key, str(self.event_manager.events[key].qsize()))

        self.session.output(tbl)

    @command(name="testevent")
    def eventsfire(self, trigger: str = "sample"):
        """Fires a test event to sample"""
        self.session.output(f"Sending test event to '{trigger}' dispatcher")
        self.dispatcher(trigger, AbacuraMessage("Notice", "TEST OF EVENT FIRING"))

    @event("sample", priority=5)
    def sampleevent(self, message: AbacuraMessage):
        self.session.output(f"I just got an event, '{message.value}'")
