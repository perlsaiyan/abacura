""" Automatic application of Buffs"""
from time import monotonic
from typing import Dict, Optional

from rich.panel import Panel
from rich.table import Table

from abacura.plugins import command, action
from abacura.plugins.events import event, AbacuraMessage
from abacura_kallisti.mud.player import PlayerSkill
from abacura_kallisti.mud.skills import SKILLS, Skill, SKILL_COMMANDS
from abacura_kallisti.plugins import LOKPlugin
from abacura.utils.renderables import AbacuraPanel, tabulate, Group, Text, OutputColors


class AutoBuff(LOKPlugin):
    """Handle application of buffs"""
    _RUNNER_INTERVAL: float = 2.0
    # _RENEWABLE_BUFS = ["true seeing", "sanctuary"]
    # _EXPIRING_BUFS = ["focus dex", "bushido"]

    def __init__(self):
        super().__init__()
        self.getting_skills: bool = False
        self.player_skills: dict[str, PlayerSkill] = {}
        self.last_attempt: Dict[str, float] = {}
        # Gods don't need buffs :)
        if self.msdp.level < 200:
            self.add_ticker(self._RUNNER_INTERVAL,
                            callback_fn=self.buff_check, repeats=-1, name="autobuff")

    def get_player_buffs(self) -> set[Skill]:
        buffs: set[Skill] = set()

        for buff in self.pc.buffs:
            skill = SKILL_COMMANDS.get(buff.lower(), None)

            if skill is None:
                self.debuglog(f"Unknown autobuff '{buff}'")
                continue

            buffs.add(skill)

        for pc_skill in self.pc.skills.values():
            if pc_skill.rank == 0:
                continue

            if pc_skill.skill.lower() not in SKILLS:
                continue

            skill: Skill = SKILLS[pc_skill.skill.lower()]
            if skill.renewal == "":
                continue

            if skill.command in buffs:
                continue

            buffs.add(skill)

        return buffs

    def buff_check(self):
        """Ticker to loop through all the buffs we know of, and renew or add ones we need"""
        if self.msdp.character_name == "" or self.msdp.level > 199:
            return

        for buff in self.get_player_buffs():
            hours = 2 if buff.renewal == 'renew' else 1
            if self.msdp.get_affect_hours(buff.affect_name or buff.skill_name) < hours:
                self.acquire_buff(buff)

        # for buf in self._RENEWABLE_BUFS:
        #     if self.msdp.get_affect_hours(buf) < 2:
        #         self.acquire_buf(buf)
        # for buf in self._EXPIRING_BUFS:
        #     if self.msdp.get_affect_hours(buf) < 1:
        #         self.acquire_buf(buf)

    def acquire_buff(self, buff: Skill):
        """Figure out how to get buf and if possible, acquire it"""
        # Only try once every 10 seconds
        if monotonic() - self.last_attempt.get(buff.command, 0) > 10:
            self.last_attempt[buff.command] = monotonic()
            method = self.acquisition_method(buff)

            if method:
                if method.startswith("-"):
                    self.cq.remove(cmd=method[1:])
                    return

                self.cq.add(cmd=method, dur=1.0, q="NCO")
            #else:
            #    self.output(f"[bold red]# No method of acquisition for {buf}!", markup=True)

    def acquisition_method(self, buff: Skill) -> Optional[str]:
        """Returns likely acquisition method"""
        if self.room.vnum in ["13200"] or self.room.no_magic or self.room.silent:
            return None

        if buff.offensive and len(self.room.mobs) > 0:
            # Nuke this command if there are mobs present as it may trigger combat
            self.debuglog(f"Skipping offensive buff '{buff.command}' when mobs present")
            return f"-{buff.command}"

        if buff.command == "focus":
            return buff.command + " dex"

        return buff.command

    @command(name="autobuff")
    def list_autobuffs(self):
        """
        Show known buffs, will add current or expected buffs or something
        """
        rows = []
        for buff in self.get_player_buffs():
            acq = self.acquisition_method(buff)
            remaining = self.msdp.get_affect_hours(buff.affect_name or buff.skill_name)
            if remaining <= 0:
                color = "orange1" if acq else "red"
                remaining = " -"
            else:
                color = "green" if remaining > 5 else "yellow"
                remaining = f"{remaining:2}"

            row = {"Buff": buff.skill_name,
                   "Hours Left": f"[{color}]{remaining}",
                   "Acquisition Method": acq,
                   "Affect": buff.affect_name}

            rows.append(row)

        pc_buffs = Text.assemble((" PC Buffs\n\n", OutputColors.section), ("  " + str(self.pc.buffs), ""))
        tbl = tabulate(rows)

        self.output(AbacuraPanel(Group(pc_buffs, Text(), tbl), title="Autobuffs"), actionable=False)

    @action(r"Skill/Spell +Cast Level +Mp.Sp +Skilled +Rank +Bonus +Damage")
    def skill_start(self):
        if not self.getting_skills:
            self.getting_skills = True
            self.player_skills = {}

    @action(r"^([a-z]+ *[a-z]*) +(\d+)* +(?:\[([^]]+)\])* +(\d+)% +(\d+)/(\d+) +\( \+*(\d+)* +\) *(\{locked\})*")
    def got_skill(self, skill: str, clevel: int, mp_sp: int, skilled: int, rank: int, trained_rank: int,
                  bonus: int, locked: str):
        if self.getting_skills:
            locked = locked is not None

            p_skill = PlayerSkill(skill.strip(), clevel, mp_sp, skilled, rank, trained_rank, bonus, locked)
            self.player_skills[p_skill.skill] = p_skill

    @action("Spell Fail Modifier: .*Skill Fail Modifier: .*")
    def end_skills(self):
        self.getting_skills = False
        self.pc.skills = self.player_skills

    @event("core.prompt", priority=10)
    def got_prompt(self, _: AbacuraMessage):
        self.getting_skills = False

    def affects(self):
        from rich.text import Text
        from rich.columns import Columns

        affects = []
        for affect in self.msdp.affects:
            affects.append(Text.assemble((f"{affect.name:15.15s}", "purple"), (f"{affect.hours:2d}", "cyan")))

        self.output(Columns(affects, width=20))
