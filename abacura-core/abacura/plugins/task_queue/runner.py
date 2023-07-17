"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""

from abacura.plugins import command, Plugin
from abacura.plugins.task_queue import _DEFAULT_PRIORITY, _DEFAULT_DURATION
from abacura.utils.tabulate import tabulate


class QueueRunner(Plugin):
    """Manage action queues by priority"""
    _RUNNER_INTERVAL: float = 0.1

    def __init__(self):
        super().__init__()
        self.cq.set_command_inserter(self.insert_command)
        self.add_ticker(self._RUNNER_INTERVAL, callback_fn=self.cq.run_queues, repeats=-1, name="Queue Runner")

    def insert_command(self, cmd: str):
        self.session.player_input(cmd, echo_color="orange1")

    def show_queues(self, q: str):
        """Show current action queue depths"""
        rows = []
        for task in self.cq._pq.queue:
            if task.q.lower().startswith(q.lower()):
                rows.append((task.q, task.cmd, task.priority, task.dur, task.delay))

        tbl = tabulate(rows, headers=("Queue", "Command", "Priority", "Duration", "Delay"),
                       title=f"Queued Commands for {q or 'all queues'}", title_justify="left")
        self.output(tbl)

    @command(name="queue")
    def queue_info(self, queue_name: str = '', cmd: str = '', _flush: bool = False,
                   _priority: int = _DEFAULT_PRIORITY, _duration: float = _DEFAULT_DURATION, _delay: int = 0):

        if _flush:
            self.cq.flush(queue_name)
            self.output(f"[bold cyan]# QUEUE: flushed '{queue_name or 'all queues'}'", markup=True, highlight=True)
            return

        if cmd == '':
            self.show_queues(q=queue_name)
            return

        self.cq.add(cmd=cmd, q=queue_name, priority=_priority, dur=_duration, delay=_delay)
        self.output(f"[bold cyan]# Command queued", markup=True, highlight=True)

    @command
    def priorities(self, n: int = 200):
        self.cq.set_qpriorities({"priority": n, "heal": 20, "combat": 30, "nco": 40, "any": 50, "move": 60})
