"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""
from abacura.plugins import command, Plugin, ticker
from abacura.plugins.task_queue import CQMessage

from abacura.plugins.task_queue import _DEFAULT_PRIORITY, _DEFAULT_DURATION
from abacura.utils.tabulate import tabulate

_RUNNER_INTERVAL: float = 0.1

class QueueRunner(Plugin):
    """Manage action queues by priority"""

    def __init__(self):
        super().__init__()
        self.cq.set_command_inserter(self.insert_command)
        #self.add_ticker(_RUNNER_INTERVAL, callback_fn=self.cq.run_queues, repeats=-1, name="Queue Runner")

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

    @ticker(seconds=_RUNNER_INTERVAL, name="Queue Runner", repeats=-1)
    def queue_runner(self):
        self.cq.run_queues()
        cqm = CQMessage()
        cqm.queue = self.cq._pq.queue
        self.dispatch(cqm)

    @command(name="queue")
    def queue_info(self, queue_name: str = '', cmd: str = '', _flush: bool = False,
                   _priority: int = _DEFAULT_PRIORITY, _duration: float = _DEFAULT_DURATION, _delay: int = 0):

        """
        Add commands to queues, display queue, or flush them

        :param queue_name: Name of queue to view or add a command
        :param cmd: The command to add
        :param _flush: Flush the queue
        :param _priority: The priority of the queue
        :param _duration: How long to wait after issuing cmd before issuing another
        :param _delay: How long to wait before issuing cmd
        """

        if _flush:
            self.cq.flush(queue_name)
            self.output(f"[bold cyan]# QUEUE: flushed '{queue_name or 'all queues'}'", markup=True, highlight=True)
            return

        if cmd == '':
            self.show_queues(q=queue_name)
            return

        self.cq.add(cmd=cmd, q=queue_name, priority=_priority, dur=_duration, delay=_delay)
        self.output("[bold cyan]# Command queued", markup=True, highlight=True)
