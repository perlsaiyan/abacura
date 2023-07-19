"""Common stuff for mud.events module"""
import inspect
from dataclasses import dataclass, field
from queue import PriorityQueue
from typing import Dict, Callable
from collections import Counter

from textual import log


@dataclass
class AbacuraMessage:
    """Base message object to pass into events"""
    event_type: str
    value: str = ""


@dataclass(order=True)
class EventTask:
    priority: int
    source: object = field(compare=False)
    handler: Callable = field(compare=False)
    trigger: str


def event(trigger: str = '', priority: int = 5):
    """Decorator for event functions"""
    def add_event(fn):
        fn.event_trigger = trigger
        fn.event_priority = priority

        return fn

    return add_event


class EventManager:
    """Load and Manage Events"""

    def __init__(self):
        log("Booting EventManager")
        self.events: Dict[str, PriorityQueue] = {}
        self.event_counts = Counter()

    def register_object(self, obj: object):
        # self.unregister_object(obj)  # prevent duplicates

        # Look for listeners in the plugin
        for member_name, member in inspect.getmembers(obj, callable):
            if hasattr(member, 'event_trigger'):
                log(f"Appending listener function '{member_name}'")
                self.add_listener(member, source=obj)

    def unregister_object(self, obj: object):
        for trigger, pq in self.events.items():
            pq.queue[:] = [e for e in pq.queue if e.source != obj]

    def add_listener(self, listener: Callable, source: object = None):
        """Add an event listener"""
        trigger: str = getattr(listener, "event_trigger")
        task = EventTask(handler=listener, source=source, trigger=trigger,
                         priority=getattr(listener, "event_priority"))

        self.events.setdefault(trigger, PriorityQueue()).put(task)

    # def get_events(self, trigger):
    #     """Return list of EventTasks in a queue"""
    #     event_list = []
    #     if trigger in self.events:
    #         newqueue = PriorityQueue()
    #
    #         while not self.events[trigger].empty():
    #             cur_event = self.events[trigger].get()
    #             newqueue.put(cur_event)
    #             event_list.append(cur_event)
    #
    #         self.events[trigger] = newqueue
    #
    #     return event_list

    def dispatch(self, message: AbacuraMessage):
        """Dispatch events"""
        if message.event_type not in self.events:
            return

        self.event_counts[message.event_type] += 1

        results = [task.handler(message) for task in self.events[message.event_type].queue]
        if len(results) == 1:
            return results[0]
