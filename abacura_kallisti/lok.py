from abacura.plugins import Plugin, command


class LegendsOfKallisti(Plugin):
    """Main plugin for LOK modules"""

    @command
    def lok(self) -> None:
        self.session.output("Legends of Kallisti!")

