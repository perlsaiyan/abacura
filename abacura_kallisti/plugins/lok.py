from abacura.plugins import command

from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.atlas.world import World
from serum import inject


class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    def __init__(self):
        super().__init__()

    @command
    def lok(self) -> None:
        self.session.output("Legends of Kallisti!")

