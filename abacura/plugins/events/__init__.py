"""Common stuff for mud.events module"""
from queue import PriorityQueue
from textual import log
from typing import Dict

from abacura import Config

class AbacuraMessage():
    """Base message object to pass into events"""
    def __init__(self, *args):
        self.type: str = args[0]
        self.value = args[1]

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
        log("Booting EventManager")
        self.events: Dict[str, PriorityQueue] = {}

    def listener(self, new_event: callable):
        """Add an event listener to a queue"""
        log(f"Appending event '{new_event.event_name}'")
        if new_event.event_name not in self.events:
            self.events[new_event.event_trigger] = PriorityQueue()

        self.events[new_event.event_trigger].put(EventTask(new_event))

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

    def dispatcher(self, trigger: str, message):
        """Dispatch events"""
        for task in self.get_events(trigger):
            log(f"Run task {task.handler} at {task.priority} with {message.value}")
            task.handler(message)
