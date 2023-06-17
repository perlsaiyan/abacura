"""LOK Communications plugins"""
from textual import log
from textual.widgets import TextLog

from abacura.plugins import Plugin, action

class LOKComms(Plugin):

    def __init__(self):
        super().__init__()

        #self.session.director.register_object(self.test_gos)
        
    @action(r"\x1B\[1;35m<Gossip: (.*)> \'(.*)\'", color=True)
    def test_gos(self, *args, **kwargs):
        commsTL = self.session.screen.query_one("#commsTL", expect_type=TextLog)
        log(f"found {commsTL} for {args[0]} and {args[1]}")
        commsTL.write(f"{args[0]}: {args[1]}")