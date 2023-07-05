from dataclasses import dataclass


RACE_CONSTRUCT = 'construct'
RACE_MINERAL = 'mineral'
RACE_UNDEAD = 'undead'
RACE_ETHEREAL = 'ethereal'
RACE_DRAGON = 'dragon'
RACE_AIR = 'air'
RACE_FISH = 'fish'
RACE_PLANT = 'plant'
RACE_INSECT = 'insect'
RACE_HUMAN = 'human'
RACE_DROW = 'drow'
RACE_TROGLODYTE = 'troglodyte'
RACE_ANIMAL = 'animal'
RACE_VAMPIRE = 'vampire'
RACE_MONSTER = 'monster'
RACE_DEMON = 'demon'
RACE_UNKNOWN = 'unknown'

ALIGN_GOOD = 'good'
ALIGN_NEUTRAL = 'neutral'
ALIGN_EVIL = 'evil'


@dataclass()
class Mob:
    name: str = ""
    starts_with: str = ''
    attack_name: str = ''
    priority: int = 10
    level: int = 0
    difficulty: int = 1
    race: str = RACE_UNKNOWN
    cls: str = 'unknown'
    alignment: str = ''
    aids: bool = False
    attacks: bool = False
    hunts: bool = False
    flees: bool = False
    blocks: bool = False
    quest: bool = False
