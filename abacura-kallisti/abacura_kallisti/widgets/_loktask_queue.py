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
        yield Static("Task Queue", classes="WidgetTitle", id="tq_title")
        yield self.queue_display

    def on_mount(self):
        self.screen.session.add_listener(self.update_task_queue)
        self.queue_display.add_column("Id", key="id")
        self.queue_display.add_column("Cmd", key="cmd")
        self.queue_display.add_column("Wait", key="wait")
        self.queue_display.add_column("Duration", key="duration")
        self.queue_display.add_column("Queue", key="queue")

    @event(CQMessage.event_type)
    def update_task_queue(self, msg: CQMessage):
        self.queue_display.clear()

        self.styles.height = len(msg.tasks) + 2

        next_task = False
        for task in msg.tasks:
            wait = ""
            if task.insertable and not next_task:
                next_task = True
                if msg.next_command_delay > 0:
                    wait = f"{msg.next_command_delay:<5.1f}s "
            elif task.wait_prior and not task.wait_prior.inserted:
                wait = f"#{task.wait_prior.id}"
            elif task.remaining_delay > 0:
                wait = f"{task.remaining_delay:<5.1f}s "
            elif task.insert_check or task._queue.insert_check:
                wait = "check()"

            self.queue_display.add_row(task.id, f"{task.cmd:15.15s}", wait, task.dur, task.q)
        self.refresh()
