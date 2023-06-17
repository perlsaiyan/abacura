"""LOK Communications plugins"""
from __future__ import annotations
from typing import Optional

from textual import log
from textual.widgets import TextLog

from abacura.mud import OutputMessage
from abacura.plugins import Plugin, action

class LOKComms(Plugin):
    comms_textlog: Optional[TextLog] = None

    @action(r"\x1B\[1;35m<Gossip: .*", color=True)
    def test_gos(self, msg: OutputMessage):
        """Send gossips to the commslog"""
        if self.comms_textlog is None:
            self.comms_textlog = self.session.screen.query_one("#commsTL", expect_type=TextLog)
        self.comms_textlog.write(f"{msg.message}")