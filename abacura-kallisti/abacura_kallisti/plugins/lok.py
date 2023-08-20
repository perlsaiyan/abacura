"""Main Legends of Kallisti Module"""
import os
import re
import time
from dataclasses import dataclass

from abacura_kallisti.plugins import LOKPlugin

from typing import Dict

from abacura.plugins.task_queue import TaskQueue
from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import action
from abacura.plugins.events import event, AbacuraMessage

xp_kill_re = re.compile("(.*) is dead!")


@dataclass
class LOKKillMessage(AbacuraMessage):
    event_type: str = "lok.kill"
    victim: str = ""
    experience: int = 0
    rare_bonus: int = 0
    reduced: bool = False

    @property
    def total_experience(self):
        return self.rare_bonus + self.experience


class LegendsOfKallisti(LOKPlugin):
    """Main plugin for LOK modules"""

    def __init__(self):
        super().__init__()
        self.add_ticker(seconds=60, callback_fn=self.idle_check, repeats=-1, name="idle-watch")

        def not_in_combat():
            return self.msdp.opponent_number == 0

        queues = {"priority": TaskQueue(10),
                  "heal": TaskQueue(20),
                  "combat": TaskQueue(30, lambda: self.msdp.opponent_number > 0),
                  "nco": TaskQueue(40, not_in_combat),
                  "any": TaskQueue(50, not_in_combat),
                  "move": TaskQueue(60, not_in_combat)
                  }
        self.cq.set_queues(queues)

        if self.session.ring_buffer:
            self.session.ring_buffer.set_log_context_provider(self.get_log_context)

        self.dispatch(AbacuraMessage(event_type="core.exec.globals", value={"lok": self.provide_lok_globals}))

    def provide_lok_globals(self) -> Dict:
        # pass additional globals to the PythonExecutor Plugin
        _globals = {"world": self.world,
                    "msdp": self.msdp,
                    "odometer": self.odometer,
                    "metrics": self.odometer.metrics,
                    "pc": self.pc,
                    "cq": self.cq,
                    "locations": self.locations,
                    "room": self.room
                    }
        return _globals

    def get_log_context(self) -> str:
        return self.msdp.room_vnum

    def idle_check(self):
        if time.monotonic() - 300 > self.session.last_socket_write:
            self.send("\n")
            #self.session.output(f"[red][italics]idle protection",markup=True)

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

    @action(r"^You receive a reduced reward for a frequent kill, only (\d+) experience points. ")
    def reduced_mob_kill(self, experience: int):
        res = self.session.ring_buffer.query(limit=1, like="%is dead!  R.I.P%")
        k_name = xp_kill_re.match(res[0][2])
        if k_name:
            msg = LOKKillMessage(victim=k_name.groups(1)[0],
                                 experience=experience, reduced=True)
            self.debuglog(msg)
            self.dispatch(msg)

    @action(r"^You receive your reward for the kill, (\d+) experience points( plus (\d+) bonus experience for a rare kill)?.")
    def mob_kill(self, experience: int, _rare_msg, rare_bonus):
        res = self.session.ring_buffer.query(limit=1, like="%is dead!  R.I.P%")
        k_name = xp_kill_re.match(res[0][2])
        if k_name:
            msg = LOKKillMessage(victim=k_name.groups(1)[0],
                                 experience=experience, rare_bonus=rare_bonus,)
            self.debuglog(msg)
            self.dispatch(msg)
