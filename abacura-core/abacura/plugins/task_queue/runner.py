"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""
from abacura.plugins import command, Plugin, ticker
from abacura.plugins.task_queue import CQMessage

from abacura.plugins.task_queue import _DEFAULT_PRIORITY, _DEFAULT_DURATION
from abacura.utils.renderables import tabulate, AbacuraPanel

_RUNNER_INTERVAL: float = 0.1


class QueueRunner(Plugin):
    """Manage action queues by priority"""

    def __init__(self):
        super().__init__()
        self.cq.set_command_inserter(self.insert_command)
        #self.add_ticker(_RUNNER_INTERVAL, callback_fn=self.cq.run_tasks, repeats=-1, name="Queue Runner")

    def insert_command(self, cmd: str):
        self.session.player_input(cmd, echo_color="orange1")

    def show_queues(self, q: str):
        """Show current action queue depths"""
        rows = []
        for task in self.cq.tasks:
            if task.q.lower().startswith(q.lower()):
                rows.append((task.id, task.q, task.cmd, task.priority, task.dur, task.delay, task.insertable))

        tbl = tabulate(rows, headers=("ID", "Queue", "Command", "Priority", "Duration", "Delay", "Insertable"),
                       title=f"Queued Commands")
        self.output(AbacuraPanel(tbl, title=f"{q or 'All Queues'}"))

    @ticker(seconds=_RUNNER_INTERVAL, name="Queue Runner", repeats=-1)
    def queue_runner(self):
        self.cq.run_tasks()
        cqm = CQMessage(tasks=self.cq.tasks, next_command_delay=self.cq.next_command_delay)
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
