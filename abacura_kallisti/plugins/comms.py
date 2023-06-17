"""LOK Communications plugins"""
from __future__ import annotations

from textual import log
from textual.widgets import TextLog

from abacura.mud import OutputMessage
from abacura.plugins import Plugin, action

class LOKComms(Plugin):

    @action(r"\x1B\[1;35m<Gossip: .*", color=True)
    def test_gos(self, msg: OutputMessage):
        """Send gossips to the commslog"""
        commsTL = self.session.screen.query_one("#commsTL", expect_type=TextLog)
        commsTL.write(f"{msg.message}")