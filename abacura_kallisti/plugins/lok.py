from abacura.plugins import command

from abacura_kallisti.plugins import LOKPlugin


class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    @command
    def lok(self) -> None:
        self.session.output("Legends of Kallisti!")

