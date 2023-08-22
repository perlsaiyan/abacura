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
        self.queue_display.add_column("Cmd", key="cmd")
        self.queue_display.add_column("Wait", key="wait")
        self.queue_display.add_column("Duration", key="duration")
        self.queue_display.add_column("Queue", key="queue")

    @event(CQMessage.event_type)
    def update_task_queue(self, msg: CQMessage):
        self.queue_display.clear()

        self.styles.height = len(msg.tasks) + 2

        def get_delay_str(delay: float) -> str:
            if delay < 1:
                return "<1s"
            return f"{int(delay):2}s "

        for task in msg.tasks:
            wait = ""
            prefix = ""
            delay = max(task.remaining_delay, msg.next_command_delay)
            color = "gray"
            if task.insertable:
                color = "bold white"
                if delay > 0:
                    wait = get_delay_str(delay)
            elif not task._queue.insertable:
                color = "orange1"
                wait = " fn()"
            elif task.wait_prior and not task.wait_prior.inserted:
                wait = f" @{task.wait_prior.cmd:5.5s}"
                prefix = " "
            elif not task.insert_check():
                wait = " fn()"
            elif delay > 0:
                wait = get_delay_str(delay)

            self.queue_display.add_row(f"[{color}]{prefix + task.cmd:15.15s}",
                                       f"[{color}]{wait}",
                                       f"[{color}]{task.dur:3.1f}",
                                       f"[{color}]{task.q}[/{color}]")
        self.refresh()
