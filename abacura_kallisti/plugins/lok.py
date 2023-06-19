from abacura.plugins import command

from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.atlas.world import World
class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    def __init__(self):
        super().__init__()
        self.session.world = World("/home/tom/world.db")

    @command
    def lok(self) -> None:
        self.session.output("Legends of Kallisti!")

