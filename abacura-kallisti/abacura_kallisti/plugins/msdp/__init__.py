from dataclasses import dataclass, field
from abacura_kallisti.mud.group import Group
from abacura_kallisti.mud.affect import Affect
from abacura_kallisti.mud.skills import SKILLS
from typing import List, Dict
import re


@dataclass(slots=True)
class TypedMSDP:
    ac: int = 0
    account_name: str = ""
    affects: List[Affect] = field(default_factory=list)
    alignment: int = 0
    ansi_colors: int = 0
    area_maxlevel: int = 0
    area_minlevel: int = 0
    area_name: str = ""
    bank_gold: int = 0
    bardsong: str = ""
    character_name: str = ""
    client_id: str = ""
    client_version: str = ""
    cls: str = ""
    combat_stance: str = ""
    con: int = 0
    con_max: int = 0
    con_perm: int = 0
    damroll: int = 0
    dex: int = 0
    dex_max: int = 0
    dex_perm: int = 0
    equipment: str = ""
    experience: int = 0
    experience_max: int = 0
    experience_tnl: int = 0
    gold: int = 0
    group: Group = field(default_factory=Group)
    grouplevel: int = 0
    health: int = 0
    health_max: int = 0
    hero_points: int = 0
    hero_points_tnl: int = 0
    hitroll: int = 0
    hold: str = ""
    hunger: int = 1
    int_: int = 0  # int is a reserved word
    int_max: int = 0
    int_perm: int = 0
    level: int = 0
    luk: int = 0
    luk_max: int = 0
    luk_perm: int = 0
    mana: int = 0
    mana_max: int = 0
    mount_health: int = 0
    mount_health_max: int = 0
    mount_name: str = ""
    mount_stamina: int = 0
    mount_stamina_max: int = 0
    mxp: int = 0
    noble_points: int = 0
    noble_points_tnl: int = 0
    opponent_health: int = 0
    opponent_health_max: int = 0
    opponent_level: int = 0
    opponent_name: str = ""
    opponent_number: int = 0
    opponent_stamina: int = 0
    opponent_stamina_max: int = 0
    paragon_level: int = 0
    pc_in_room: int = 0
    pc_in_zone: int = 0
    plugin_id: str = ""
    position: str = ""
    practice: int = 0
    prompt: str = ""
    qpoints: int = 0
    queue: int = 0
    quickdraw: str = ""
    race: str = ""
    ranged: int = 0
    remort_levels: str = ""  # coming soon
    remort_laps_in_class: int = 0
    remort_laps_total: int = 0
    reportable_variables: str = ""
    room_exits: Dict = field(default_factory=dict)
    room_name: str = ""
    room_terrain: str = ""
    room_vnum: str = ""
    room_weather: str = ""
    server_id: str = ""
    server_time: int = 0
    shield: str = ""
    snippet_version: int = 0
    sound: int = 0
    stamina: int = 0
    stamina_max: int = 0
    str_: int = 0  # str is a reserved word
    str_max: int = 0
    str_perm: int = 0
    thirst: int = 1
    uptime: int = 0
    utf_8: int = 0
    whoflags: str = ""
    wield: str = ""
    wimpy: int = 0
    wis: int = 0
    wis_max: int = 0
    wis_perm: int = 0
    world_time: int = 0
    xterm_256_colors: int = 0

    @property
    def hp(self) -> int:
        return self.health

    @property
    def hp_max(self) -> int:

        return self.health_max

    @property
    def mp(self) -> int:
        return self.mana

    @property
    def mp_max(self) -> int:
        return self.mana_max

    @property
    def sp(self) -> int:
        return self.stamina

    @property
    def int(self) -> int:
        return self.int_

    @property
    def str(self):
        return self.str_

    @property
    def sp_max(self) -> int:
        return self.stamina_max

    @property
    def hp_pct(self) -> float:
        return 100 * self.hp / max(1, self.hp_max)

    @property
    def mp_pct(self) -> float:
        return 100 * self.mp / max(1, self.mp_max)

    @property
    def sp_pct(self) -> float:
        return 100 * self.sp / max(1, self.sp_max)

    @property
    def opponent_hp(self) -> int:
        return self.opponent_health

    @property
    def opponent_hp_max(self) -> int:
        return self.opponent_health_max

    @property
    def opponent_sp(self) -> int:
        return self.opponent_stamina

    @property
    def opponent_sp_max(self) -> int:
        return self.opponent_stamina_max

    @property
    def mount_hp(self) -> int:
        return self.mount_health

    @property
    def mount_hp_max(self) -> int:
        return self.mount_health_max

    @property
    def mount_sp(self) -> int:
        return self.mount_stamina

    @property
    def mount_sp_max(self) -> int:
        return self.mount_stamina_max
    
    def get_affect_hours(self, affect_name: str) -> int:
        # lowercase and drop anything after the first space to handle 'focus dex', 'warpaint crimson', etc
        affect_name = affect_name.split(' ')[0]

        # handle case where command is different from spell name
        # darmor -> Divine Armor, aura -> Unholy Aura, etc

        skill = SKILLS.get(affect_name.lower(), None)
        affect_pattern: str = skill.affect_name if skill is not None else affect_name

        for a in self.affects:
            # print(a, a.hours, affect_name)
            if re.match(affect_pattern, a.name, re.IGNORECASE):
                return int(a.hours)

        return 0
    #
    # def get_exits(self) -> Dict:
    #     e = tintin.parse_table(self.room_exits)
    #     return e
    #
    # def get_group(self) -> Group:
    #     return Group(self.group)
