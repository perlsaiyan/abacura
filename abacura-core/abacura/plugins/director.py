from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Callable

from abacura.plugins.actions import ActionManager
from abacura.plugins.aliases.manager import AliasManager
from abacura.plugins.commands import CommandManager
from abacura.plugins.events import EventManager
from abacura.plugins.tickers import TickerManager

if TYPE_CHECKING:
    from abacura.mud.session import Session


@dataclass()
class Registration:
    registration_type: str
    name: str
    callback: Callable
    details: str


class Director:
    def __init__(self, session: Session):
        self.session = session
        self.action_manager: ActionManager = ActionManager()
        self.command_manager: CommandManager = CommandManager(session)
        self.ticker_manager: TickerManager = TickerManager()
        self.alias_manager: AliasManager = AliasManager(session)
        self.event_manager: EventManager = EventManager()

    def register_object(self, obj: object):
        if getattr(obj, "register_actions", True):
            self.action_manager.register_object(obj)

        self.ticker_manager.register_object(obj)
        self.command_manager.register_object(obj)
        self.event_manager.register_object(obj)

    def unregister_object(self, obj: object):
        self.action_manager.unregister_object(obj)
        self.ticker_manager.unregister_object(obj)
        self.command_manager.unregister_object(obj)
        self.event_manager.unregister_object(obj)

    def get_registrations_for_object(self, obj: object) -> List:
        registrations: List[Registration] = []

        for act in self.action_manager.actions.queue:
            if act.source == obj:
                registrations.append(Registration("action", act.name, act.callback, act.pattern))

        for tkr in self.ticker_manager.tickers:
            if tkr.source == obj:
                detail = f"seconds={tkr.seconds}, repeats={tkr.repeats}"
                registrations.append(Registration("ticker", tkr.name, tkr.callback, detail))

        for cmd in self.command_manager.commands:
            if cmd.source == obj:
                registrations.append(Registration("command", cmd.name, cmd.callback, cmd.get_description()))

        # Create lookup of members
        for trigger, pq in self.event_manager.events.items():
            for et in pq.queue:
                if et.source == obj:
                    registrations.append(Registration("event", et.trigger, et.handler, f"priority={et.priority}"))

        return registrations
