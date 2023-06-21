import os

from abacura.plugins import command, action
from abacura_kallisti.plugins import LOKPlugin


class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    def __init__(self):
        super().__init__()

    @command
    def lok(self) -> None:
        self.session.output("Legends of Kallisti!")

    @action(r'^Please enter your account password')
    def send_password(self):
        if os.environ.get("MUD_PASSWORD") is not None:
            self.session.send(os.environ.get("MUD_PASSWORD"))

    @action(r'^Enter your account name. If you do not have an account,')
    def send_account_name(self):
        account = self.config.get_specific_option(self.session.name, "account_name")
        if account:
            self.session.send(account)
