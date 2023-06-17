from abacura.plugins import Plugin, command


class PluginMeta(Plugin):
    @command
    def meta(self) -> None:
        """Hyperlink demo"""
        self.session.output("Meta info blah blah")
        self.session.output("Obtained from https://kallisti.nonserviam.net/hero-calc/Pif")
