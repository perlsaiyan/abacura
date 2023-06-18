from abacura.plugins import command

from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.plugins.msdp import LOKMSDP


class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    @command
    def lok(self) -> None:
        self.session.output("Legends of Kallisti!")

