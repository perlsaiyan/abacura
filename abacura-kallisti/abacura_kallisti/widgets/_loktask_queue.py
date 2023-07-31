"""Kallisti widget for displaying Task Queue information"""
from textual.app import ComposeResult
from textual.widgets import Static, DataTable


from abacura.plugins.events import event
from abacura.plugins.task_queue import CQMessage

class LOKTaskQueue(Static):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_display = DataTable(show_cursor=False)
        self.queue_display.can_focus = False

    def compose(self) -> ComposeResult:
        yield Static("Task Queue",classes="WidgetTitle", id="tq_title")
        yield self.queue_display

    def on_mount(self):
        self.screen.session.add_listener(self.update_task_queue)
        self.queue_display.add_column("Cmd", key="cmd")
        self.queue_display.add_column("Delay", key="delay")
        self.queue_display.add_column("Duration", key="duration")
        self.queue_display.add_column("Queue", key="queue")

    @event(CQMessage.event_type)
    def update_task_queue(self, msg: CQMessage):
        self.queue_display.clear()

        for task in msg.queue:
            self.queue_display.add_row(f"{task.cmd:15.15s}", task.delay, task.dur, task.q)
