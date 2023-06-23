"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""

from functools import partial
from queue import PriorityQueue
from time import monotonic
from datetime import datetime
from typing import List, Dict, Optional, Callable

from textual import log
from abacura.mud.session import Session
from abacura.plugins import command, action

from abacura_kallisti.plugins import LOKPlugin

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

class QueueManager:
    """Manage action queues by priority"""

    _QUEUE_NAMES: List = ["Priority", "Combat", "NCO", "Any", "Move"]
    _QUEUES: Dict[str, PriorityQueue] = {}
    _DEFAULT_PRIORITY: int = 50
    _NEXT_COMMAND_TIME: float = 0.0
    _DEFAULT_DURATION: float = 1.0
    _command_inserter: Optional[Callable] = None

    def __init__(self):
        super().__init__()
        self.initialize_queues()
        self._command_inserter = None

    def initialize_queues(self, qn: Optional[str] = None, silent: bool = True):
        """Initialize the Action Priority Queues"""
        if qn is None:
            for queue in self._QUEUE_NAMES:
                self._QUEUES[queue] = PriorityQueue()
        elif qn in self._QUEUES:
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
                if self._command_inserter:
                    self._command_inserter(task.cmd)
                    log(f"Sent {task.cmd} inserted at {task.insert_time}")
                else:
                    log.error(f"No command inserter present for {task.cmd}")

                self._NEXT_COMMAND_TIME = monotonic() + task.dur
                return

    def add(self, task: QueueTask, queue_name: str = "Any", priority: int = _DEFAULT_PRIORITY):
        if queue_name and queue_name in self._QUEUE_NAMES:
            self._QUEUES[queue_name].put((priority, task))
        else:
            raise Exception("Invalid Queue")

    @property
    def default_priority(self):
        return self._DEFAULT_PRIORITY

    @property
    def default_duration(self):
        return self._DEFAULT_DURATION
    
    def set_command_inserter(self, f: Callable):
        self._command_inserter = f
    
class LOKQueueRunner(LOKPlugin):
    """Manage action queues by priority"""
    _default_priority: float = 50
    _DEFAULT_DURATION: float = 1.0
    _RUNNER_INTERVAL: float = 0.1

    def __init__(self):
        super().__init__()
        self._default_priority = self.cq.default_priority
        self._DEFAULT_DURATION = self.cq.default_duration

        self.cq.set_command_inserter(self.session.player_input)
        self.add_ticker(self._RUNNER_INTERVAL, callback_fn=self.cq.run_queues, repeats=-1, name="Queue Runner")

    @command(name="queue")
    def queueinfo(self):
        """Show current action queue depths"""
        for queue_name, queue in self.cq._QUEUES.items():
            self.output(f"Queue '{queue_name}' has depth {queue.qsize()}.", markup=True, highlight=True)

    @command(name="addqueue")
    def add_to_queue(self, task: str ,queue_name: str = "Any", priority: int = _default_priority, dur: float = _DEFAULT_DURATION):
        """Adds an individual task with an optional priority to a queue"""
        try:
            self.cq.add(priority=priority, queue_name=queue_name, task=QueueTask(task, dur=dur)) 
        except InvalidQueueName:
            self.output("[bold red]# Invalid queue", markup=True)
        except Exception as exc:
            self.session.show_exception("Failed to add task", exc, show_tb=True)
        return

    @command(name="flushqueue")
    def flush_the_queues(self, qn: Optional[str] = None):
        """Flush the action queues, optional qn for a specific queue"""
        try:
            self.cq.initialize_queues(qn=qn)
        except InvalidQueueName:
            self.output(f"[bold red]# Queue error: invalid queue '{qn}'", markup=True, highlight=True)
            return
        if qn:
            self.output(f"[bold cyan]# QUEUE: flushed '{qn}'", markup=True, highlight=True)
        else:
            self.output("[bold cyan]# QUEUE: flushed all queues", markup=True, highlight=True)