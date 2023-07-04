"""Common stuff for mud.events module"""
from dataclasses import dataclass
import inspect
from queue import PriorityQueue
from typing import Dict

from textual import log

from abacura import Config

@dataclass
class AbacuraMessage:
    """Base message object to pass into events"""
    event_type: str
    value: str = ""

class EventTask:
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


class EventManager:
    """Load and Manage Events"""

    config: Config

    def __init__(self):
        log("Booting EventManager")
        self.events: Dict[str, PriorityQueue] = {}

    def register_object(self, obj):
        # Look for listeners in the plugin
        for member_name, member in inspect.getmembers(obj, callable):
            if hasattr(member, 'event_name'):
                log(f"Appending listener function '{member_name}'")
                self.listener(member)

    def unregister_object(self, obj):
        for member_name, member in inspect.getmembers(obj, callable):
            if hasattr(member, 'event_name'):
                log(f"Removing listener function '{member_name}'")
                self.remove_listener(member)

    def remove_listener(self, event_handler: callable):
        if event_handler.event_trigger in self.events:
            try:
                self.events[event_handler.event_trigger].queue.remove(event_handler)
            except ValueError:
                log(f"Listener not found when unregistering {event_handler} from {event_handler.event_trigger}")

    def listener(self, new_event: callable):
        """Add an event listener to a queue"""
        if new_event.event_trigger not in self.events:
            self.events[new_event.event_trigger] = PriorityQueue()

        self.events[new_event.event_trigger].put(EventTask(new_event))

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

    def dispatcher(self, message: AbacuraMessage):
        """Dispatch events"""
        if message.event_type not in self.events:
            return

        for task in self.events[message.event_type].queue:
            task.handler(message)
