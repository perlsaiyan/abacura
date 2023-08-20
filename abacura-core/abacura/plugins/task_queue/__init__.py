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

from abacura.plugins.events import AbacuraMessage


class InvalidQueueName(Exception):
    pass


_DEFAULT_PRIORITY = 50
_DEFAULT_DURATION: float = 1.0


@dataclass
class TaskQueue:
    priority: int = _DEFAULT_PRIORITY
    insertable: Callable = lambda: True


@dataclass
class Task:
    cmd: str = ""
    dur: float = 1
    q: str = "any"
    priority: int = _DEFAULT_PRIORITY
    delay: float = 0
    insert_time: float = field(default_factory=monotonic)
    _queue: TaskQueue = field(default_factory=TaskQueue, init=True)

    @property
    def insertable(self):
        return self._queue.insertable() and monotonic() >= self.insert_time + self.delay

    @property
    def overall_priority(self):
        return self._queue.priority, self.priority, self.insert_time

    def __lt__(self, other):
        return self.overall_priority < other.overall_priority

    def set_queue(self, queue: TaskQueue):
        self._queue = queue


@dataclass
class CQMessage(AbacuraMessage):
    event_type: str = "lok.cqmessage"
    value: str = ""
    tasks: list[Task] = field(default_factory=list)


class TaskManager:
    """Manage tasks by priority"""

    def __init__(self, queues: Dict[str, TaskQueue] | None = None):
        self._pq: PriorityQueue[Task] = PriorityQueue()
        self._NEXT_COMMAND_TIME: float = 0.0
        self._command_inserter: Optional[Callable] = None
        self._queues: dict[str, TaskQueue] = {}

        if queues:
            self._queues = queues

    @property
    def tasks(self) -> list[Task]:
        return self._pq.queue

    def set_queues(self, queues: Dict[str, TaskQueue]):
        self._queues = queues

        # update queues for each task and re-sort in case priorities changed
        for task in self._pq.queue:
            task._queue = queues.get(task.q, TaskQueue())

        self._pq.queue.sort()

    def get_next_insertable_task(self) -> Task | None:
        # Process these in queue priority order
        for i, task in enumerate(self._pq.queue):
            if not task.insertable:
                continue

            # Note, popping mutates the list we are iterating, but we are returning so no problem...
            self._pq.queue.pop(i)
            return task

        return None

    def run_tasks(self):
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

    def flush(self, q: str = ''):
        if q == '':
            self._pq = PriorityQueue()
            return

        # change list in place
        self._pq.queue[:] = [task for task in self._pq.queue if task.q.lower() != q.lower()]

    def add_task(self, task: Task):
        task.set_queue(self._queues.get(task.q, TaskQueue()))
        self._pq.put(task)
        self.run_tasks()

    def add(self, cmd: str, q: str = "any",
            priority: int = _DEFAULT_PRIORITY, dur: float = _DEFAULT_DURATION, delay: float = 0):
        self.add_task(Task(cmd=cmd, priority=priority, dur=dur, delay=delay, q=q))

    def set_command_inserter(self, f: Callable):
        self._command_inserter = f

    def remove(self, cmd: str):
        for task in self._pq.queue:
            if task.cmd.lower() == cmd.lower():
                self._pq.queue.remove(task)
