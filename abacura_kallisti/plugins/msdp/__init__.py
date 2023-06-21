from dataclasses import dataclass, field
from abacura_kallisti.mud.group import Group


@dataclass(slots=True)
class TypedMSDP:
    reportable_variables: str = ""
    uptime: int = 0
    world_time: int = 0
    name: str = ""
    level: int = 0
    cls: str = ""
    race: str = ""
    alignment: int = 0
    hp: int = 0
    hp_max: int = 0
    mp: int = 0
    mp_max: int = 0
    sp: int = 0
    sp_max: int = 0
    wimpy: int = 0
    xp: int = 0
    xp_max: int = 0
    xp_tnl: int = 0
    gold: int = 0
    bank: int = 0
    ac: int = 0
    hitroll: int = 0
    damroll: int = 0
    group: Group = field(default_factory=Group)
    affects: str = ""
    ranged: int = 0
    stance: str = ""
    position: str = ""
    strength: int = 0
    intelligence: int = 0
    wisdom: int = 0
    dexterity: int = 0
    constitution: int = 0
    luck: int = 0
    hero: int = 0
    hero_tnl: int = 0
    opponent_level: int = 0
    opponent_name: str = ""
    opponent_number: int = 0
    opponent_hp: int = 0
    opponent_hp_max: int = 0
    opponent_sp: int = 0
    opponent_sp_max: int = 0
    area_name: str = ""
    area_max_level: int = 0
    area_min_level: int = 0
    room_vnum: str = ""
    room_name: str = ""
    room_exits: str = ""
    room_terrain: str = ""
    mount_hp: int = 0
    mount_hp_max: int = 0
    mount_sp: int = 0
    mount_sp_max: int = 0
    mount_name: str = ""
    hunger: int = 1
    thirst: int = 1
    wield: str = ""
    shield: str = ""
    hold: str = ""
    quickdraw: str = ""
    pc_in_area: int = 0
    pc_in_room: int = 0
    prompt_flags: str = ""
    bardsong: str = ""

    def get_hp_pct(self) -> float:
        return 100 * self.hp / max(1, self.hp_max)

    def get_mp_pct(self) -> float:
        return 100 * self.mp / max(1, self.mp_max)

    def get_sp_pct(self) -> float:
        return 100 * self.sp / max(1, self.sp_max)

    # def get_affects(self) -> List[Affect]:
    #     ad = tintin.parse_table(self.affects)
    #     # print(self.affects)
    #     # print(ad)
    #     affects: List[Affect] = []
    #     for name, hours in ad.items():
    #         affects.append(Affect(name=name, hours=int(hours)))
    #     return affects
    #
    # def get_affect_hours(self, affect_name: str) -> int:
    #     # lowercase and drop anything after the first space to handle 'focus dex', 'warpaint crimson', etc
    #     affect_name = affect_name.split(' ')[0]
    #
    #     # handle case where command is different from spell name
    #     # darmor -> Divine Armor, aura -> Unholy Aura, etc
    #     skill = SKILLS.get(affect_name.lower(), None)
    #     affect_pattern: str = skill.affect_name if skill is not None else affect_name
    #
    #     for a in self.get_affects():
    #         # print(a, a.hours, affect_name)
    #         if re.match(affect_pattern, a.name, re.IGNORECASE):
    #             return a.hours
    #
    #     return 0
    #
    # def get_exits(self) -> Dict:
    #     e = tintin.parse_table(self.room_exits)
    #     return e
    #
    # def get_group(self) -> Group:
    #     return Group(self.group)
