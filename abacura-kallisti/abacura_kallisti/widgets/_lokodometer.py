"""Kallisti widget for displaying Odometer information"""
from datetime import datetime
from textual.app import ComposeResult
from textual.widgets import Static, DataTable


from abacura.plugins.events import event
from abacura.utils import human_format
from abacura_kallisti.metrics.odometer import OdometerMessage

class LOKOdometer(Static):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_display = DataTable(show_cursor=False)

    def compose(self) -> ComposeResult:
        yield Static("Odometers",classes="WidgetTitle", id="tq_title")
        yield self.queue_display

    def on_mount(self):
        self.screen.session.add_listener(self.update_odometers)
        self.queue_display.add_column("Mission", key="mission")
        self.queue_display.add_column("Elapsed", key="elapsed")
        self.queue_display.add_column("Kills/h", key="kills")
        self.queue_display.add_column("XP/h", key="xp")
        self.queue_display.add_column("$/h", key="gold")

    @event(OdometerMessage.event_type)
    def update_odometers(self, msg: OdometerMessage):
        self.queue_display.clear()

        odometer_list = msg.odometer[-5:]
        odometer_list.reverse()
        for odometer in odometer_list:
            self.queue_display.add_row(
                odometer.mission,
                datetime.utcfromtimestamp(odometer.elapsed).strftime('%H:%M:%S'),
                human_format(odometer.kills_per_hour),
                human_format(odometer.xp_per_hour),
                human_format(odometer.gold_per_hour),
            )
