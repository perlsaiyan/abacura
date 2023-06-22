from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class Skill:
    command: str
    affect_name: Optional[str]
    min_level: Dict[str, int] = field(default_factory=dict)
    cls_level: Dict[str, int] = field(default_factory=dict)
    sp_base: int = 0
    sp_level_mult: float = 0
    sp_rank_mult: int = 0
    mp: int = 0
    prompt_flag: Optional[str] = None
    delay: int = 2
    offensive: bool = False
    follower: str = ''


# TODO: Add in required sp / mp for future use
SKILL_LIST: List[Skill] = [
    Skill('bifrost', None, {'Valkyrie': 75}),
    Skill('deathknell', None, {'Dreadlord': 33}, delay=2),
    Skill('layhands', None, {'Paladin': 11}),
    Skill('kick', None, {'Monastic': 1, 'Samurai': 1, 'Monk': 1,
                         'Fighter': 1, 'Barbarian': 1,  'Paladin': 1, 'Valkyrie': 1, 'Dreadlord': 1, 'Ranger': 1,
                         'Rogue': 4, 'Demoniac': 4, 'Bard': 4, 'Assassin': 4}, delay=2),
    Skill('heal', None, {'Templar': 1, 'Priest': 1, 'Druid': 1, 'Prophet': 1}, delay=2),
    Skill('pheal', None, {'Templar': 33, 'Prophet': 33}),
    Skill('fheal', None, {'Prophet': 58, 'Templar': 60}),
    Skill('hillsborough halfstep', None, {'Bard': 31}),
    Skill('march', None, {'Bard': 41}),
    Skill('meditate', None, {'Templar': 29, 'Monk': 16, 'Monastic': 16, 'Samurai': 16, 'Prophet': 43}),
    Skill('miracle', None, {'Prophet': 17, 'Templar': 22}),
    Skill('cure', None, {'Prophet': 9, 'Templar': 9, 'Priest': 9, 'Druid': 9}),
    Skill('refresh', None, {'Druid': 4, 'Prophet': 4, 'Priest': 4, 'Templar': 4}),
    Skill('dehydrate', None, {'Druid': 27, 'Necromancer': 20}),
    Skill('bless', 'Bless', {'Templar': 7, 'Prophet': 7, 'Druid': 7, 'Priest': 7}),
    Skill('true', 'True Seeing', {'Templar': 8, 'Prophet': 8, 'Druid': 8, 'Priest': 8, 'Valkyrie': 50}),
    Skill('blade', 'Blade Barrier', {'Templar': 53}),
    Skill('barkskin', 'Barkskin', {'Druid': 11}),
    Skill('spirit', 'Spiritual guardian', {"Templar": 51, 'Prophet': 39}),
    Skill('vigor', 'Vigor', {'Druid': 26, 'Prophet': 26, 'Priest': 26, 'Templar': 26}),
    Skill('haste', 'Haste', {'Wizard': 23}),
    Skill('zap', None, {'Mage': 1, 'Wizard': 1, 'Necromancer': 1}),
    Skill('ctouch', None, {'Mage': 10, 'Wizard': 10, 'Necromancer': 10}),
    Skill('strength', 'Strength', {'Mage': 2, 'Wizard': 2, 'Necromancer': 2}),
    Skill('familiar', 'Familiar', {'Mage': 5, 'Wizard': 5, 'Necromancer': 5}, follower='familiar'),
    Skill('pfg', 'Protection from good', {'Demoniac': 33}),
    Skill('drain', None, {'Demoniac': 20}),
    Skill('dragonstrike', None, {'Samurai': 33, 'Monk': 43}),
    Skill('deadeyes', 'Deadeyes', {'Demoniac': 26}),
    Skill('bloodlust', 'Bloodlust', {'Demoniac': 40}),
    Skill('soul syphon', None, {'Demoniac': 28}),
    Skill('warcry', 'Warcry', {'Valkyrie': 45, 'Barbarian': 40}),
    Skill('wraithform', 'Wraithform', {'Dreadlord': 70}),
    Skill('aura', 'Unholy aura', {'Dreadlord': 60}),
    Skill('bind', None, {'Ranger': 21, 'Barbarian': 60, 'Assassin': 27}),
    Skill('smount', 'Call Mount', {'Druid': 26}),
    Skill('impale', None, {'Ranger': 33, 'Valkyrie': 36, 'Samurai': 37}),
    Skill('prayer', 'Prayer', {'Paladin': 40}),
    Skill('bushido', 'Spirit of bushido', {'Samurai': 55}),
    Skill('charge', None, {'Valkyrie': 42, 'Fighter': 42, 'Dreadlord': 42, 'Ranger': 42, 'Paladin': 42,
                           'Barbarian': 42, 'Samurai': 50}),
    Skill('werewolf', 'Shapechange'),
    Skill('call mount', 'Call Mount', {'Dreadlord': 21, 'Paladin': 21, 'Ranger': 23, 'Valkyrie': 27}),
    Skill('sanctuary', 'Sanctuary', {'Paladin': 70, 'Prophet': 16, 'Templar': 17}),
    Skill('darmor', 'Divine Armor', {'Prophet': 10, 'Templar': 11}),
    Skill('dshield', 'Divine shield', {'Paladin': 50, 'Templar': 70}),
    Skill('wio', None, {'Valkyrie': 30}),
    Skill('mead', None, {'Valkyrie': 10}),
    Skill('valmeyjar', 'Haste', {'Valkyrie': 32}, offensive=True),
    Skill('valravn', None, {'Valkyrie': 40}),
    Skill('assimilate', None, {'Dreadlord': 16}),
    Skill('purify', None, {'Monk': 55, 'Ranger': 70, 'Valkyrie': 70}),
    Skill('fdk', None, {'Monk': 50}, delay=2),
    Skill('fst', None, {'Druid': 29, 'Templar': 25}, delay=2),
    Skill('endurance', None, {'Valkyrie': 44, 'Barbarian': 44, 'Ranger': 29, 'Monk': 29}),
    # focus dex , for wilderness especially
    Skill('grimward', 'Grim ward', {'Demoniac': 60}),
    Skill('demonform', 'Shapechange.*', {'Demoniac': 49}),
    Skill('focus', 'Focus', {'Monk': 18, 'Monastic': 18, 'Samurai': 18,
                             'Ranger': 40, 'Barbarian': 36, 'Valkyrie': 34,
                             'Assassin': 75, 'Bard': 75}),
    # Druid shapechanges that are useful in wilderness
    Skill('shapechange plant', 'Shapechange', {'Druid': 42}),
    Skill('shapechange mammoth', 'Shapechange', {'Druid': 49}),
    Skill('shapechange wyvern', 'Shapechange', {'Druid': 60}),
    Skill('shapechange frost dragon', 'Shapechange', {'Druid': 65}),
    Skill('shapechange star dragon', 'Shapechange', {'Druid': 70}),
    Skill('shapechange copper dragon', 'Shapechange', {'Druid': 75}),
    Skill('shapechange mantis dragon', 'Shapechange', {'Druid': 100}),
    Skill('carve', None, sp_base=0, sp_level_mult=1.3, sp_rank_mult=3),
    Skill('bonecraft', None, sp_base=0, sp_level_mult=1.3, sp_rank_mult=3),
    Skill('armorcraft', None, sp_base=0, sp_level_mult=1.3, sp_rank_mult=3),
    Skill('skin', None, sp_base=120, sp_level_mult=1, sp_rank_mult=5),
    Skill('chirurgy', None, sp_base=120, sp_level_mult=1, sp_rank_mult=5),
    Skill('butcher', None, sp_base=40, sp_level_mult=1, sp_rank_mult=5),
    Skill('tan', None, sp_base=0, sp_level_mult=1.7, sp_rank_mult=5),
    Skill('mill', None, sp_base=0, sp_level_mult=1.7, sp_rank_mult=5),
    Skill('forge', None, sp_base=0, sp_level_mult=1.7, sp_rank_mult=5),
    Skill('earthquake', None, {'Templar': 42, 'Druid': 50}),
    Skill('battou jutsu', None, {'Samurai': 52})
    ]

# create a lookup dictionary
SKILLS: Dict[str, Skill] = {s.command: s for s in SKILL_LIST}


BUTCHER_SKILL_ITEMS = {'extract': 'bone', 'skin': 'hide', 'butcher': 'meat'}
