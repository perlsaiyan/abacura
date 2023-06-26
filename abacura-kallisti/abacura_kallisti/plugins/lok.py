import os
import time

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import command, action
from abacura.plugins.events import event

from abacura_kallisti.plugins import LOKPlugin


class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    def __init__(self):
        super().__init__()
        #self.add_ticker(seconds=60, callback_fn=self.idle_check, repeats=-1, name="idle-watch")
        
    def idle_check(self):
        if time.monotonic() - 300 > self.session.last_socket_write:
            self.session.send("\n")
            #self.session.output(f"[red][italics]idle protection",markup=True)

    # @command
    # def lok(self) -> None:
    #     self.session.output("Legends of Kallisti!")

    @action(r'^Please enter your account password')
    def send_password(self):
        if os.environ.get("MUD_PASSWORD") is not None:
            self.session.send(os.environ.get("MUD_PASSWORD"))

    @action(r'^Enter your account name. If you do not have an account,')
    def send_account_name(self):
        account = self.config.get_specific_option(self.session.name, "account_name")
        if account:
            self.session.send(account)

    @event("msdp_value")
    def update_pc(self, msg: MSDPMessage):
        # PC_FIELDS = ["level"]
        # if msg.type in PC_FIELDS:
        #     setattr(self.pc, msg.type, msg.value)
        
        # reload config, we've changed people
        if msg.type == "CHARACTER_NAME":
            self.output(f"[orange1][italic]# Reloading player conf for {msg.value}", markup=True)
            self.pc.load(self.config.data_directory(self.session.name), msg.value)
