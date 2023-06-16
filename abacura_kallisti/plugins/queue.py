"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""

from functools import partial
from queue import PriorityQueue
from time import monotonic
from datetime import datetime
from typing import List, Dict, Optional

from textual import log
from abacura.plugins import Plugin, command, action

class InvalidQueueName(Exception):
    pass

class QueueTask():
    def __init__(self, cmd: str = "", dur: Optional[float] = 1):
        """QueueTasks are individual items submitted to the QueueManager"""
        self.cmd = cmd
        self.dur = dur
        self.insert_time = datetime.utcnow()
    
    def __lt__(self, other):
        return self.insert_time < other.insert_time

    def __gt__(self, other):
        return self.insert_time > other.insert_time

    def __eq__(self, other):
        return self.insert_time == other.insert_time
    
class LOKQueueRunner(Plugin):
    """Manage action queues by priority"""

    _QUEUE_NAMES: List = ["Priority", "Combat", "NCO", "Any", "Move"]
    _RUNNER_INTERVAL: float = 0.1
    _QUEUES: Dict[str, PriorityQueue] = {}
    _DEFAULT_PRIORITY: int = 50
    _NEXT_COMMAND_TIME: float = 0.0
    _DEFAULT_DURATION: float = 1.0

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
        if monotonic() < self._NEXT_COMMAND_TIME:
            return

        for (queue_name, queue) in self._QUEUES.items():

            if not queue.empty():
                _, task = queue.get()
                self.session.player_input(task.cmd)
                log(f"Sent {task.cmd} inserted at {task.insert_time}")
                self._NEXT_COMMAND_TIME = monotonic() + task.dur
                return


    @command(name="queue")
    def queueinfo(self):
        """Show current action queue depths"""
        for queue_name, queue in self._QUEUES.items():
            self.session.output(f"Queue '{queue_name}' has depth {queue.qsize()}.", markup=True, highlight=True)

    @command(name="queueadd")
    def add_to_queue(self, qn: str, command: str, priority: int = _DEFAULT_PRIORITY, dur: float = _DEFAULT_DURATION):
        """Adds an individual task with an optional priority to a queue"""
        if qn in self._QUEUE_NAMES:
        
            self._QUEUES[qn].put((priority, QueueTask(cmd=command, dur=dur)))
            return
        
        self.session.output("[bold red]# ERROR: Invalid queue name")

    @command(name="queueflush")
    def flush_the_queues(self, qn: Optional[str] = None):
        """Flush the action queues, optional qn for a specific queue"""
        try:
            self.initialize_queues(qn=qn, silent=False)
        except InvalidQueueName:
            self.session.output(f"[bold red]# Queue error: invalid queue '{qn}'", markup=True, highlight=True)
