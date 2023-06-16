"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""

from functools import partial
from queue import PriorityQueue
from time import monotonic
from typing import List, Dict, Optional
from abacura.plugins import Plugin, command, action

class InvalidQueueName(Exception):
    pass

class LOKQueueRunner(Plugin):
    """Manage action queues by priority"""

    _QUEUE_NAMES: List = ["Priority", "Combat", "NCO", "Any", "Move"]
    _RUNNER_INTERVAL: int = 1
    _QUEUES: Dict[str, PriorityQueue] = {}
    _DEFAULT_PRIORITY: int = 50
    _LAST_COMMAND_TIME: float = 0

    def __init__(self):
        super().__init__()
        self.initialize_queues()
        self.add_ticker(self._RUNNER_INTERVAL, callback_fn=self.run_queues, repeats=-1, name="Queue Runner")
    
    def initialize_queues(self, qn: Optional[str] = None, silent: bool = True):
        """Initialize the Action Priority Queues"""
        if qn is None:
            if not silent:
                self.session.output("[bold cyan]# Flushing all action queues", markup = True)
            for queue in self._QUEUE_NAMES:
                self._QUEUES[queue] = PriorityQueue()
        elif qn in self._QUEUES:
            if not silent:
                self.session.output(f"[bold cyan]# Flushing action queue '{qn}'", markup = True, highlight=True)
            self._QUEUES[qn] = PriorityQueue()
        else:
            raise InvalidQueueName

    def run_queues(self):
        """This is the actual queue runner routine"""
        if monotonic() - 2 < self._LAST_COMMAND_TIME:
            return
        
        for (queue_name, queue) in self._QUEUES.items():
            if not queue.empty():
                self.session.output(f"[bold cyan]Queue '{queue_name}': {queue.qsize()}", markup=True, highlight=True)
                task = queue.get()
                self.session.output(f"[bold cyan] perform '{task[1]}' from priority {task[0]}", markup=True, highlight=True)
                self._LAST_COMMAND_TIME = monotonic()
                return

    @command(name="queueadd")
    def add_to_queue(self, qn: str, command: str, priority: int = _DEFAULT_PRIORITY):
        """Adds an individual task with an optional priority to a queue"""
        if qn in self._QUEUE_NAMES:
            self._QUEUES[qn].put((priority, command))
            return
        
        self.session.output("[bold red]# ERROR: Invalid queue name")

    @command(name="queueflush")
    def flush_the_queues(self, qn: Optional[str] = None):
        """Flush the action queues, optional qn for a specific queue"""
        try:
            self.initialize_queues(qn=qn, silent=False)
        except InvalidQueueName:
            self.session.output(f"[bold red]# Queue error: invalid queue '{qn}'", markup=True, highlight=True)
