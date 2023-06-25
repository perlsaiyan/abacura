"""The Event plugin"""
from abacura.plugins import Plugin, command
from abacura.plugins.events import event, AbacuraMessage


class EventPlugin(Plugin):
    """Commands and things """

    def __init__(self):
        super().__init__()
        self.dispatcher = self.session.dispatcher
        self.event_manager = self.session.director.event_manager

    @command(name="events")
    def eventscommand(self):
        """Show events"""
        for key in self.event_manager.events.keys():
            self.session.output(f"{key}: {self.event_manager.events[key].qsize()} events")

    @command(name="testevent")
    def eventsfire(self, trigger: str = "sample"):
        """Fires a test event to sample"""
        self.session.output(f"Sending test event to '{trigger}' dispatcher")
        self.dispatcher(trigger, AbacuraMessage("Notice", "TEST OF EVENT FIRING"))

    @event("sample", priority=5)
    def sampleevent(self, message: AbacuraMessage):
        self.session.output(f"I just got an event, '{message.value}'")
