"""Common stuff for mud.events module"""
from queue import PriorityQueue
from typing import Dict

from abacura import Config

class AbacuraMessage():
    """Base message object to pass into events"""
    def __init__(self, type, value):
        self.type = type
        self.value = value

class EventTask():
    """Class to support queue-able events"""
    def __init__(self, handler):
        self.priority = handler.priority
        self.handler = handler

    def __lt__(self, other):
        return self.priority < other.priority
    def __gt__(self, other):
        return self.priority > other.priority
    def __eq__(self, other):
        return self.priority == other.priority

def event(trigger: str = '', priority: int = 5):
    """Decorator for event functions"""
    def add_event(fn):

        fn.event_name = fn.__name__
        fn.event_trigger = trigger
        fn.priority = priority

        return fn

    return add_event

class EventManager():
    """Load and Manage Events"""

    config: Config

    def __init__(self):
        self.events: Dict[str, PriorityQueue] = {}

    def listener(self, event_name: str, new_event):
        """Add an event listener to a queue"""
        if event_name not in self.events:
            self.events[event_name] = PriorityQueue()

        self.events[event_name].put(EventTask(new_event))

    def get_events(self, trigger):
        """Return list of EventTasks in a queue"""
        event_list = []
        if trigger in self.events:
            newqueue = PriorityQueue()

            while not self.events[trigger].empty():
                cur_event = self.events[trigger].get()
                newqueue.put(cur_event)
                event_list.append(cur_event)
            self.events[trigger] = newqueue
            return event_list
        return event_list

    def dispatcher(self, trigger: str, message: AbacuraMessage):
        """Dispatch events"""
        for task in self.get_events(trigger):
            print(f"Run task {task.handler} at {task.priority}")
            task.handler(message)
