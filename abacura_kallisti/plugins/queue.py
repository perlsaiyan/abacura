"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""

from functools import partial
from queue import PriorityQueue
from time import monotonic
from typing import List, Dict
from abacura.plugins import Plugin, command, action

class LOKQueueRunner(Plugin):
    """Manage action queues by priority"""

    QUEUE_NAMES: List = ["Priority", "Combat", "NCO", "Move"]
    RUNNER_INTERVAL: int = 1
    QUEUES: Dict[str, PriorityQueue] = {}
    DEFAULT_PRIORITY: int = 50
    LAST_COMMAND_TIME: float = 0

    def __init__(self):
        super().__init__()

        for queue in self.QUEUE_NAMES:
            self.QUEUES[queue] = PriorityQueue()

        self.add_ticker(self.RUNNER_INTERVAL, callback_fn=self.run_queues, repeats=-1, name="Queue Runner")
    
    def run_queues(self):
        """This is the actual queue runner routine"""
        if monotonic() - 2 < self.LAST_COMMAND_TIME:
            return
        
        for qn in self.QUEUE_NAMES:
            if self.QUEUES[qn].qsize():
                self.session.output(f"[bold cyan]Queue '{qn}': {self.QUEUES[qn].qsize()}", markup=True, highlight=True)
                task = self.QUEUES[qn].get()
                self.session.output(f"[bold cyan] perform '{task[1]}' from priority {task[0]}", markup=True, highlight=True)
                self.LAST_COMMAND_TIME = monotonic()
                return

    @command(name="queueadd")
    def add_to_queue(self, qn: str, command: str, priority: int = DEFAULT_PRIORITY):
        """Adds an individual task with an optional priority to a queue"""
        if qn in self.QUEUE_NAMES:
            self.QUEUES[qn].put((priority, command))
            return
        
        self.session.output("[bold red]# ERROR: Invalid queue name")
