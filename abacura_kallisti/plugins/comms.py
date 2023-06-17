"""LOK Communications plugins"""
from textual.widgets import TextLog

from abacura.plugins import Plugin, action

class LOKComms(Plugin):

    def __init__(self):
        super().__init__()

        self.session.director.register_object(self.test_gos)
        
    @action(r"\x1B\[1;35m<Gossip: (.*)> \'(.*)\'")
    def test_gos(self, *args, **kwargs):
        commsTL = self.screen.query_one("#commsTL", expected_type=TextLog)
        commsTL.write(f"{args[0]}: {args[1]}")