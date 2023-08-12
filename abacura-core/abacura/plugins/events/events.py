"""The Event plugin"""
from abacura.plugins import Plugin, command, CommandError
from abacura.plugins.events import AbacuraMessage
from abacura.utils.renderables import tabulate, AbacuraPanel

class EventPlugin(Plugin):
    """Commands and things """

    @command(name="events")
    def eventscommand(self, name: str = ''):
        """
        Show event metrics and handlers

        :param name: Show handlers for this event name
        """
        event_manager = self.session.director.event_manager

        if name:
            keys = [key for key in event_manager.events.keys() if key.lower().startswith(name.lower())]
            exact = [key for key in keys if key.lower() == name.lower()]
            if len(keys) > 1 and len(exact) > 1:
                raise CommandError(f"Ambiguous event name '{name}'")
            if len(keys) == 0:
                raise CommandError(f"Unknown event name '{name}'")

            rows = []
            show_event = exact[0] if len(exact) else keys[0]

            for key, value in event_manager.events.items():
                if key != show_event:
                    continue

                for f in value.queue:
                    rows.append({"Priority": f.priority, "Module": f.handler.__module__, "Method": f.handler.__name__})

            self.output(AbacuraPanel(tabulate(rows), title=show_event))
            return

        rows = []
        for key, value in event_manager.events.items():
            row = {"Event Name": key,
                   "# Handlers": value.qsize(),
                   "# Events Processed": event_manager.event_counts[key]}

            # if detail:
            #     row['Handlers'] = [f"{str(f.handler.__module__)}.{str(f.handler.__name__)}" for f in value.queue]

            rows.append(row)

        self.output(AbacuraPanel(tabulate(rows), title="Events"))

    @command(name="dispatch")
    def dispatch_event(self, trigger: str, value: str = ""):
        """
        Dispatch an AbacuraMessage

        :param trigger: The event to trigger
        :param value: A value to send with the event
        """
        self.session.output(f"Sending {trigger} message: {value}")
        self.dispatch(AbacuraMessage(trigger, value))
