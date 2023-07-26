from datetime import datetime

from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.metrics.odometer import OdometerMessage

from abacura.plugins import command, action, ticker
from abacura.plugins.events import AbacuraMessage
from abacura.plugins.events import event
from abacura.utils import human_format
from abacura.utils.tabulate import tabulate


class OdometerController(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.last_kill = ""
        self.last_skill = ""

    @command(name="odometer")
    def odometer_command(self, clear: bool = False, _start: bool = False, _mission: str = "") -> None:
        """Display Odometer History"""

        if clear:
            self.odometer.clear_history()
            self.output("[orange1]Odometer Reset!", markup=True)
            return

        if _start:
            if _mission == '':
                _mission = self.msdp.area_name

            self.odometer.start(mission=_mission)
            self.output(f"[orange1]Odometer started! ({_mission})", markup=True)
            return

        if _mission:
            self.metrics.mission = _mission
            self.output(f"[orange1]Odometer Mission set to '{_mission}'", markup=True)
            return

        rows = []
        for i, m in enumerate(reversed(self.odometer.metric_history)):
            rows.append((len(self.odometer.metric_history) - i,
                         m.mission,
                         m.start_time.strftime("%H:%M:%S"),
                         datetime.utcfromtimestamp(m.elapsed).strftime('%H:%M:%S'),
                         m.kills_per_hour,
                         human_format(m.xp_per_hour), human_format(m.gold_per_hour)
                         ))

        headers = ["#", "Mission", "Start", "Elapsed", "Kills/h", "XP/h", "$/h"]
        self.output(tabulate(rows, headers=headers))

    @ticker(seconds=1, name="Odometer")
    def odometer_ticker(self):
        if len(self.odometer.metric_history) == 0 and self.msdp.character_name != '':
            self.debuglog("Starting initial odometer")
            self.odometer.start(mission=self.msdp.area_name)

        om = OdometerMessage()
        om.odometer = self.odometer.metric_history
        self.dispatch(om)

    @action(r"^(.*) is dead!.*R.I.P.")
    def killed(self, mob: str):
        self.last_kill = mob
        self.metrics.kills += 1

    @event("core.prompt", priority=1)
    def got_prompt(self, _: AbacuraMessage):
        self.last_kill = ''
        self.last_skill = ''

    @action(r"^You gain (\d+) experience for mastering a skill.")
    def skill_exp(self, xp: int):
        self.metrics.earn_xp('practice', xp, area=self.msdp.area_name, vnum=self.msdp.room_vnum)

    @action(r"^You receive a reduced reward for a frequent kill, only (\d+) experience points.")
    def killed_reduced_exp(self, xp: int):
        self.metrics.earn_xp('kill-reduced', xp, self.last_kill, area=self.msdp.area_name, vnum=self.msdp.room_vnum)

    @action(r"^You receive your reward for the kill, (\d+) experience points\.")
    def killed_exp(self, xp: int):
        self.metrics.earn_xp('kill', xp, self.last_kill, area=self.msdp.area_name, vnum=self.msdp.room_vnum)

    @action(r"^You receive your reward for the kill, (\d+) experience points plus (\d+) bonus experience for a rare")
    def killed_rare_exp(self, kill_xp: int, rare_xp: int):
        self.metrics.earn_xp('kill', kill_xp, self.last_kill, area=self.msdp.area_name, vnum=self.msdp.room_vnum)
        self.metrics.earn_xp('kill-rare', rare_xp, self.last_kill, area=self.msdp.area_name, vnum=self.msdp.room_vnum)

    @action(r"^There were (\d+) coins")
    def coins(self, gold: int):
        source = "kill" if self.last_kill else ""
        self.metrics.earn_gold(source, gold, self.last_kill, self.msdp.area_name, self.msdp.room_vnum)

    @action(r"^You (mine|gather|chop down|catch|skin|butcher|extract) some (.*) " +
            "(herbs|cotton|silk|ore|wood|fish|meat|hide|bone)")
    def harvested(self, skill: str, quality: str, _material: str):
        self.metrics.craft_attempted += 1
        self.metrics.craft_successful += 1
        self.metrics.craft_qualities[quality] += 1
        self.last_skill = skill

    @action(r"^You earn (.*) experience points")
    def exp(self, xp: int):
        self.metrics.earn_xp(self.last_skill, xp, area=self.msdp.area_name, vnum=self.msdp.room_vnum)

    @action(r"^You can't seem to find anything nearby.")
    def nothing_nearby(self):
        self.metrics.craft_attempted += 1

    @action(r"^You deposit (.*) coins.")
    def deposit_coins(self, coins: int):
        self.metrics.counters['deposit'] += coins

    @event("core.msdp.EXPERIENCE")
    def msdp_xp(self, _: AbacuraMessage):
        self.metrics.end_xp = self.msdp.experience

    @event("core.msdp.GOLD")
    def msdp_gold(self, _: AbacuraMessage):
        self.metrics.end_gold = self.msdp.gold

    @event("core.msdp.BANK_GOLD")
    def msdp_bank(self, _: AbacuraMessage):
        self.metrics.end_bank = self.msdp.bank_gold
