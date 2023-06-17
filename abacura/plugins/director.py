from __future__ import annotations

from typing import TYPE_CHECKING

from serum import inject, Context

from abacura.plugins.actions import ActionManager
from abacura.plugins.commands import CommandManager
from abacura.plugins.tickers import TickerManager
from abacura.plugins.aliases.manager import AliasManager

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

    def register_object(self, obj: object):
        self.action_manager.register_object(obj)
        self.ticker_manager.register_object(obj)
        self.command_manager.register_object(obj)

    def unregister_object(self, obj: object):
        self.action_manager.unregister_object(obj)
        self.ticker_manager.unregister_object(obj)
        self.command_manager.unregister_object(obj)
