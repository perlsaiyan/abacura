from dataclasses import dataclass
import os
import re
import time


from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import command, action
from abacura.plugins.events import event, AbacuraMessage

from abacura_kallisti.plugins import LOKPlugin

xp_kill_re = re.compile("(.*) is dead!")

@dataclass
class LOKKillMessage(AbacuraMessage):
    event_type: str = "lok.kill"
    victim: str = ""
    experience: int = 0

class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    def __init__(self):
        super().__init__()
        self.add_ticker(seconds=60, callback_fn=self.idle_check, repeats=-1, name="idle-watch")
        
    def idle_check(self):
        if time.monotonic() - 300 > self.session.last_socket_write:
            self.send("\n")
            #self.session.output(f"[red][italics]idle protection",markup=True)

    # @command
    # def lok(self) -> None:
    #     self.session.output("Legends of Kallisti!")

    @action(r'^Please enter your account password')
    def send_password(self):
        if os.environ.get("MUD_PASSWORD") is not None:
            self.send(os.environ.get("MUD_PASSWORD"), echo_color='')

    @action(r'^Enter your account name. If you do not have an account,')
    def send_account_name(self):
        account = self.config.get_specific_option(self.session.name, "account_name")
        if account:
            self.send(account, echo_color='')

    @event("core.msdp")
    def update_pc(self, msg: MSDPMessage):
        # PC_FIELDS = ["level"]
        # if msg.type in PC_FIELDS:
        #     setattr(self.pc, msg.type, msg.value)
        
        # reload config, we've changed people
        if msg.subtype == "CHARACTER_NAME":
            self.debuglog(facility="info", msg=f"Reloading player conf for '{msg.value}'")
            self.pc.load(self.config.data_directory(self.session.name), msg.value)
            self.director.alias_manager.load(f"{self.session.name}.aliases")

    @action(r"^You receive your reward for the kill, (\d+) experience points.")
    def mob_kill(self, experience: int):
        res = self.session.ring_buffer.query(limit=1, like="%is dead!  R.I.P%")
        k_name = xp_kill_re.match(res[0][2])
        if k_name:
            msg = LOKKillMessage(victim=k_name.groups(1)[0], experience=experience)
            self.session.dispatcher(msg)
