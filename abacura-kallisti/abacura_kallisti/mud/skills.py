from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Skill:
    skill_name: str
    command: str = ''
    affect_name: str = ''
    renewal: str = ''
    train: Dict[str, int] = field(default_factory=dict)
    sp_base: int = 0
    sp_level_mult: float = 0
    sp_rank_mult: int = 0
    delay: int = 2
    offensive: bool = False
    follower: str = ''
    
    def __post_init__(self):
        self.command = self.command or self.skill_name
        self.affect_name = self.affect_name or self.skill_name

    def __hash__(self):
        return hash(self.skill_name)


SKILL_LIST: List[Skill] = [
    Skill("bifrost", train={"Valkyrie": 75}),
    Skill("deathknell", train={"Dreadlord": 33}, delay=2),
    Skill("layhands", train={"Paladin": 11}),
    Skill("kick", train={"Monastic": 1, "Samurai": 1, "Monk": 1,
                         "Fighter": 1, "Barbarian": 1,  "Paladin": 1,
                         "Valkyrie": 1, "Dreadlord": 1, "Ranger": 1,
                         "Rogue": 4, "Demoniac": 4, "Bard": 4, "Assassin": 4}, delay=2),
    Skill("heal", train={"Templar": 1, "Priest": 1, "Druid": 1, "Prophet": 1}, delay=2),
    Skill("power heal", command="pheal", train={"Templar": 33, "Prophet": 33}),
    Skill("full heal", command="fheal", train={"Prophet": 58, "Templar": 60}),
    Skill("hillsborough halfstep", command="play hills", train={"Bard": 31}),
    Skill("march", command="play march", train={"Bard": 41}),
    Skill("meditate", train={"Templar": 29, "Monk": 16, "Monastic": 16, "Samurai": 16, "Prophet": 43}),
    Skill("miracle", train={"Prophet": 17, "Templar": 22}),
    Skill("cure", train={"Prophet": 9, "Templar": 9, "Priest": 9, "Druid": 9}),
    Skill("refresh", train={"Druid": 4, "Prophet": 4, "Priest": 4, "Templar": 4}),
    Skill("dehydrate", train={"Druid": 27, "Necromancer": 20}),
    Skill("bless", renewal="renew", train={"Templar": 7, "Prophet": 7, "Druid": 7, "Priest": 7}),
    Skill("true seeing", command="truesee", renewal="renew",
          train={"Templar": 8, "Prophet": 8, "Druid": 8, "Priest": 8, "Valkyrie": 50}),
    Skill("blade barrier", command="blade", renewal="renew", train={"Templar": 53}),
    Skill("barkskin", renewal="renew", train={"Druid": 11}),
    Skill("spiritual guardian", command="spirit", renewal="expire", train={"Templar": 51, "Prophet": 39}),
    Skill("vigor", renewal="renew", train={"Druid": 26, "Prophet": 26, "Priest": 26, "Templar": 26}),
    Skill("haste", renewal="renew", train={"Wizard": 23}),
    Skill("zap", train={"Mage": 1, "Wizard": 1, "Necromancer": 1}),
    Skill("chill touch", "ctouch", train={"Mage": 10, "Wizard": 10, "Necromancer": 10}),
    Skill("strength", renewal="renew", train={"Mage": 2, "Wizard": 2, "Necromancer": 2}),
    Skill("familiar", renewal="expire", train={"Mage": 5, "Wizard": 5, "Necromancer": 5}, follower="familiar"),
    Skill("protection from good", "pfg", renewal="renew", train={"Demoniac": 33}),
    Skill("drain", train={"Demoniac": 20}),
    Skill("dragonstrike", train={"Samurai": 33, "Monk": 43}),
    Skill("deadeyes", renewal="renew", train={"Demoniac": 26}),
    Skill("bloodlust", "Bloodlust", renewal="renew", train={"Demoniac": 40}),
    Skill("soul syphon", train={"Demoniac": 28}),
    Skill("warcry", "warcry", renewal="renew", train={"Valkyrie": 45, "Barbarian": 40}),
    Skill("wraithform", "Wraithform", renewal="renew", train={"Dreadlord": 70}),
    Skill("aura", "Unholy aura", renewal="renew", train={"Dreadlord": 60}),
    Skill("bind", train={"Ranger": 21, "Barbarian": 60, "Assassin": 27}),
    Skill("smount", "Call Mount", "", train={"Druid": 26}),
    Skill("impale", train={"Ranger": 33, "Valkyrie": 36, "Samurai": 37}),
    Skill("prayer", "Prayer", "", train={"Paladin": 40}),
    Skill("Spirit of bushido", "bushido", affect_name="spirit of bushido", train={"Samurai": 55}),
    Skill("charge", train={"Valkyrie": 42, "Fighter": 42, "Dreadlord": 42, "Ranger": 42, "Paladin": 42,
                           "Barbarian": 42, "Samurai": 50}),
    Skill("werewolf", affect_name="shapechange"),
    Skill("call mount", train={"Dreadlord": 21, "Paladin": 21, "Ranger": 23, "Valkyrie": 27}),
    Skill("sanctuary", renewal="renew", train={"Paladin": 70, "Prophet": 16, "Templar": 17}),
    Skill("divine armor", command="darmor", renewal="renew", train={"Prophet": 10, "Templar": 11}),
    Skill("divine shield", command="dshield", renewal="expire", train={"Paladin": 50, "Templar": 70}),
    Skill("wio", train={"Valkyrie": 30}),
    Skill("mead", train={"Valkyrie": 10}),
    Skill("valmeyjar", affect_name="haste", renewal="expire", train={"Valkyrie": 32}, offensive=True),
    Skill("valravn", train={"Valkyrie": 40}),
    Skill("assimilate", train={"Dreadlord": 16}),
    Skill("purify", train={"Monk": 55, "Ranger": 70, "Valkyrie": 70}),
    Skill("fdk", train={"Monk": 50}, delay=2),
    Skill("fst", train={"Druid": 29, "Templar": 25}, delay=2),
    Skill("endurance", train={"Valkyrie": 44, "Barbarian": 44, "Ranger": 29, "Monk": 29}),
    # focus dex , for wilderness especially
    Skill("grim ward", "grimward", renewal="renew", train={"Demoniac": 60}),
    Skill("demonform", affect_name="Shapechange.*", renewal="expire", train={"Demoniac": 49}),
    Skill("focus", renewal="renew", train={"Monk": 18, "Monastic": 18, "Samurai": 18,
                                           "Ranger": 40, "Barbarian": 36, "Valkyrie": 34,
                                           "Assassin": 75, "Bard": 75}),
    # Druid shapechanges that are useful in wilderness
    Skill("shapechange plant", affect_name="shapechange", renewal="renew", train={"Druid": 42}),
    Skill("shapechange mammoth", affect_name="shapechange", renewal="renew", train={"Druid": 49}),
    Skill("shapechange wyvern", affect_name="shapechange", renewal="renew", train={"Druid": 60}),
    Skill("shapechange frost dragon", affect_name="shapechange", renewal="renew", train={"Druid": 65}),
    Skill("shapechange star dragon", affect_name="shapechange", renewal="renew", train={"Druid": 70}),
    Skill("shapechange copper dragon", affect_name="shapechange", renewal="renew", train={"Druid": 75}),
    Skill("shapechange gold dragon", affect_name="shapechange", renewal="renew", train={"Druid": 75}),
    Skill("shapechange mantis dragon", affect_name="shapechange", renewal="renew", train={"Druid": 100}),
    Skill("earthquake", train={"Templar": 42, "Druid": 50}),
    Skill("battou jutsu", train={"Samurai": 52}),
    Skill("carve", "", sp_base=0, sp_level_mult=1.3, sp_rank_mult=3),
    Skill("bonecraft", "", sp_base=0, sp_level_mult=1.3, sp_rank_mult=3),
    Skill("armorcraft", "", sp_base=0, sp_level_mult=1.3, sp_rank_mult=3),
    Skill("skin", "", sp_base=120, sp_level_mult=1, sp_rank_mult=5),
    Skill("chirurgy", "", sp_base=120, sp_level_mult=1, sp_rank_mult=5),
    Skill("butcher", "", sp_base=40, sp_level_mult=1, sp_rank_mult=5),
    Skill("tan", "", sp_base=0, sp_level_mult=1.7, sp_rank_mult=5),
    Skill("mill", "", sp_base=0, sp_level_mult=1.7, sp_rank_mult=5),
    Skill("forge", "", sp_base=0, sp_level_mult=1.7, sp_rank_mult=5)
    ]

# create a lookup dictionary
SKILLS: Dict[str, Skill] = {s.skill_name: s for s in SKILL_LIST}
SKILL_COMMANDS: Dict[str, Skill] = {s.command: s for s in SKILL_LIST}

BUTCHER_SKILL_ITEMS = {'extract': 'bone', 'skin': 'hide', 'butcher': 'meat'}
