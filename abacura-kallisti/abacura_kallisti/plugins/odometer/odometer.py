from abacura.plugins import command, action
from abacura.plugins.events import AbacuraMessage
from abacura.plugins.events import event
from abacura.utils.tabulate import tabulate
from abacura_kallisti.metrics import EarnedGold, EarnedXP
from abacura_kallisti.plugins import LOKPlugin


class OdometerController(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.last_kill = ""
        self.last_skill = ""

    @command(name="odometer")
    def odometer_command(self, reset: bool = False, _start: str = "", _stop: bool = False) -> None:
        """Display Odometer History"""

        if reset:
            self.odometer.reset_history()
            self.output("[orange1]Odometer Reset!", markup=True)
            return

        if _start != "":
            self.odometer.start(mission=_start)
            self.output(f"[orange1]Odometer Started! ({_start})", markup=True)
            return

        if _stop:
            self.odometer.stop()
            self.output("[orange1]Odometer Stopped!", markup=True)
            return

        rows = []
        for i, m in enumerate(self.odometer.metric_history):
            rows.append((i, m.mission, m.elapsed, m.xp_per_hour, m.gold_per_hour))

        headers = ["#", "Mission", "Elapsed", "XP/h", "$/h"]
        self.output(tabulate(rows, headers=headers))

    def earn_xp(self, xp_source: str, xp: int, victim: str = ''):
        if self.metrics.stop_time is None:
            self.metrics.earned_xp.append(EarnedXP(source=xp_source, xp=xp, victim=victim))

    def earn_gold(self, gold_source: str, gold: int, victim: str = ''):
        if self.metrics.stop_time is None:
            self.metrics.earned_gold.append(EarnedGold(source=gold_source, gold=gold, victim=victim))

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
        self.earn_xp('practice', xp)

    @action(r"^You receive a reduced reward for a frequent kill, only (\d+) experience points.")
    def killed_reduced_exp(self, xp: int):
        self.earn_xp('kill-reduced', xp, victim=self.last_kill)

    @action(r"^You receive your reward for the kill, (\d+) experience points\.")
    def killed_exp(self, xp: int):
        self.earn_xp('kill', xp, victim=self.last_kill)

    @action(r"^You receive your reward for the kill, (\d+) experience points plus (\d+) bonus experience for a rare")
    def killed_rare_exp(self, kill_xp: int, rare_xp: int):
        self.earn_xp('kill', kill_xp, victim=self.last_kill)
        self.earn_xp('kill-rare', rare_xp, victim=self.last_kill)

    @action(r"^There were (\d+) coins")
    def coins(self, gold: int):
        self.earn_gold("kill" if self.last_kill else "", gold=gold, victim=self.last_kill)

    @action(r"^You (mine|gather|chop down|catch|skin|butcher|extract) some (.*) " +
            "(herbs|cotton|silk|ore|wood|fish|meat|hide|bone)")
    def harvested(self, skill: str, quality: str, _material: str):
        if self.metrics.stop_time is None:
            self.metrics.craft_attempted += 1
            self.metrics.craft_successful += 1
            self.last_skill = skill
            self.metrics.craft_qualities[quality] += 1

    @action(r"^You deposit (.*) coins.")
    def deposit_coins(self, coins: int):
        if self.metrics.stop_time is None:
            self.metrics.counters['deposit'] += coins

    @action(r"^You can't seem to find anything nearby.")
    def nothing_nearby(self):
        if self.metrics.stop_time is None:
            self.metrics.craft_attempted += 1

    @action(r"^You earn (.*) experience points")
    def exp(self, xp: int):
        self.earn_xp(self.last_skill, xp)
