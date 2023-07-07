from __future__ import annotations

from typing import TYPE_CHECKING

from serum import inject, Context

from abacura.plugins.actions import ActionManager
from abacura.plugins.commands import CommandManager
from abacura.plugins.tickers import TickerManager
from abacura.plugins.aliases.manager import AliasManager
from abacura.plugins.events import EventManager
from abacura.plugins.scripts import ScriptManager, ScriptProvider


if TYPE_CHECKING:
    from abacura.mud.session import Session


@inject
class Director:
    session: Session

    def __init__(self):
        with Context(session=self.session):
            self.action_manager: ActionManager = ActionManager()
            self.command_manager: CommandManager = CommandManager()
            self.ticker_manager: TickerManager = TickerManager()
            self.alias_manager: AliasManager = AliasManager()
            self.event_manager: EventManager = EventManager()
            self.script_manager: ScriptManager = ScriptManager()

        self.script_provider = ScriptProvider(self.script_manager)

    def register_object(self, obj: object):
        if getattr(obj, "register_actions", True):
            self.action_manager.register_object(obj)

        self.ticker_manager.register_object(obj)
        self.command_manager.register_object(obj)
        self.event_manager.register_object(obj)
        self.script_manager.register_object(obj)

    def unregister_object(self, obj: object):
        self.action_manager.unregister_object(obj)
        self.ticker_manager.unregister_object(obj)
        self.command_manager.unregister_object(obj)
        self.event_manager.unregister_object(obj)
        self.script_manager.unregister_object(obj)
