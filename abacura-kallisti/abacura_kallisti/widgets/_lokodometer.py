"""Kallisti widget for displaying Odometer information"""
from datetime import datetime
from typing import List

from rich.pretty import Pretty

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.events import MouseDown, MouseUp, MouseMove, Click
from textual.widgets import Static, DataTable

from abacura_kallisti.metrics import MudMetrics
from abacura.plugins.events import event
from abacura.utils import human_format
from abacura_kallisti.metrics.odometer import OdometerMessage

class LOKOdometerDetailWindow(ScrollableContainer):

    def __init__(self, odometer: MudMetrics, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._moving: bool = False
        self.odometer = self.summarize(odometer)
        self.styles.height = 10

    def compose(self) -> ComposeResult:
        yield Static(self.odometer)

    def summarize(self, odometer: MudMetrics) -> str:
        buf = []
        buf.append(f"[cyan]Mission Started: [white]{odometer.start_time}  [cyan]Ended: [white]{odometer.stop_time}")
        buf.append(f"[cyan]Mobs killed: [white]{odometer.kills} @ {odometer.kills_per_hour:.1f} per hour")
        buf.append(f"[cyan]Gold earned: [white]{human_format(odometer.earned_gold)} @ {human_format(odometer.gold_per_hour)} per hour")

        buf.append(f"[cyan]XP Earned: [white]{human_format(odometer.earned_xp)} @ {human_format(odometer.xp_per_hour)} per hour")
        buf.append(f"[cyan]Crafting: [white]{odometer.craft_qualities}")
        buf.append(f"[cyan]Rests: [white]{odometer.rests} [cyan]for [white]{odometer.rest_time}")
        return "\n".join(buf)

    def on_mouse_down(self, event: MouseDown):
        if self.disabled or self._moving:
            return
        self.capture_mouse()
        self._moving = True
        self._start_mouse_position = event.screen_offset
        self.add_class("-active")

    def on_mouse_up(self, event: MouseUp):
        self.release_mouse()
        self._moving = False
        self._start_mouse_position = None
        self.remove_class("-active")

    def on_mouse_move(self, event: MouseMove):
        if not self._moving:
            return
        self.offset += event.delta

    def on_click(self, event: Click):
        if event.button == 3:
            self.remove()

class LOKOdometer(Static):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_display = DataTable(show_cursor=False, id="odometer_table")
        self.queue_display.cursor_type = "row"
        #self.queue_display.can_focus = False
        self.styles.height = 7
        #self.can_focus = False
        #self.can_focus_children = False
        self.odometers: List[MudMetrics] = []

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
        self.odometers = odometer_list
        for odometer in odometer_list:
            self.queue_display.add_row(
                odometer.mission,
                datetime.utcfromtimestamp(odometer.elapsed).strftime('%H:%M:%S'),
                human_format(odometer.kills_per_hour),
                human_format(odometer.xp_per_hour),
                human_format(odometer.gold_per_hour),
            )

    def on_click(self, event: Click) -> None:
        if len(self.odometers) < 1:
            return
        
        row = event.y-1
        if row >= 0 and row < len(self.odometers):
            detail = LOKOdometerDetailWindow(odometer = self.odometers[row], classes="popover odometer-detail")
            detail.styles.offset = (event.screen_x + 10, event.screen_y + 2)
            self.screen.mount(detail)
