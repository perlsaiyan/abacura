"""
Command Queue running routines

Tracks last command, calculates delay, and issues commands in priority order,
depending on the combat situation.
"""

from dataclasses import dataclass, field
from queue import PriorityQueue
from time import monotonic
from typing import Optional, Callable, Dict

from textual import log


class InvalidQueueName(Exception):
    pass


_DEFAULT_PRIORITY = 50
_DEFAULT_DURATION: float = 1.0


@dataclass
class QueueTask:
    cmd: str = ""
    dur: float = 1
    q: str = "any"
    priority: int = _DEFAULT_PRIORITY
    delay: float = 0
    insert_time: float = field(default_factory=monotonic)
    _qpriorities: dict[str, int] = field(default_factory=dict, repr=False, init=False)

    def overall_priority(self):
        return self._qpriorities.get(self.q.lower(), 100), self.priority, self.insert_time

    def __lt__(self, other):
        return self.overall_priority() < other.overall_priority()


class QueueManager:
    """Manage action queues by priority"""

    def __init__(self, qpriorities: Dict[str, int] | None = None):
        self._pq: PriorityQueue[QueueTask] = PriorityQueue()
        self._NEXT_COMMAND_TIME: float = 0.0
        self._command_inserter: Optional[Callable] = None

        self._qpriorities = {}

        if qpriorities:
            self._qpriorities = qpriorities

    def set_qpriorities(self, qpriorities: Dict[str, int]):
        # keep current instance in case it is pointed at by Tasks
        # this allows instantly changing priorities
        self._qpriorities = qpriorities
        for task in self._pq.queue:
            task._qpriorities = qpriorities
        self._pq.queue.sort()

    def get_next_insertable_task(self) -> QueueTask | None:
        # Process these in queue priority order
        for i, task in enumerate(self._pq.queue):
            if monotonic() < task.insert_time + task.delay:
                continue

            # Note, popping mutates the list we are iterating, but we are returning so no problem...
            self._pq.queue.pop(i)
            return task

        return None

    def run_queues(self):
        """This is the actual queue runner routine"""

        if self._command_inserter is None:
            log.error(f"No command inserter")
            return

        # process as many tasks as we can
        while self._NEXT_COMMAND_TIME < monotonic():
            task = self.get_next_insertable_task()
            if task is None:
                break

            self._command_inserter(task.cmd)
            log(f"Sent {task.cmd} inserted at {task.insert_time}")
            self._NEXT_COMMAND_TIME = monotonic() + task.dur

    def flush(self, qn: str = ''):
        if qn == '':
            self._pq = PriorityQueue()
            return

        for i, task in enumerate(self._pq.queue):
            if task.q.lower() == qn.lower():
                self._pq.queue.pop(i)

    def add_task(self, task: QueueTask):
        task._qpriorities = self._qpriorities
        self._pq.put(task)
        self.run_queues()

    def add(self, cmd: str, q: str = "any",
            priority: int = _DEFAULT_PRIORITY, dur: float = _DEFAULT_DURATION, delay: float = 0):
        self.add_task(QueueTask(cmd=cmd, priority=priority, dur=dur, delay=delay, q=q))

    def set_command_inserter(self, f: Callable):
        self._command_inserter = f
