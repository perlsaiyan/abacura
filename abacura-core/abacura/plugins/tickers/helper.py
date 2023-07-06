from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from abacura.plugins import Plugin, command, CommandError

if TYPE_CHECKING:
    pass


class TickerCommand(Plugin):

    @command
    def ticker(self, name: str, message: str = '', seconds: float = 0, repeats: int = -1, delete: bool = False):
        """Create/delete a ticker"""
        if not message:
            raise CommandError("Must specify a message")

        if seconds <= 0:
            raise CommandError("Seconds must be more than 0")

        # always remove an existing ticker with this name
        self.remove_ticker(name)
        if delete:
            return

        self.add_ticker(seconds=seconds, callback_fn=partial(self.session.output, msg=message),
                        repeats=repeats, name=name)
