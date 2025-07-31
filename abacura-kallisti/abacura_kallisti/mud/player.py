"""
Player structure

Includes current player information, and preferences
"""
from dataclasses import dataclass, field, fields
import os
from typing import Dict
from tomlkit import parse, TOMLDocument, document, table

@dataclass(slots=True)
class PlayerSkill:
    skill: str = ""
    clevel: int = 0
    mp_sp: int = 0
    skilled: int = 0
    rank: int = 0
    trained_rank: int = 0
    rank_bonus: int = 0
    locked: bool = False


@dataclass
class PlayerHarvesting:
    """Toggles for harvesting skills"""

    butchering: bool = False
    chirurgy: bool = False
    fishing: bool = False
    gathering: bool = False
    logging: bool = False
    poisoncraft: bool = False
    skinning: bool = False


@dataclass(slots=True)
class PlayerCharacter:
    """Kallisti specific player information"""

    _config: TOMLDocument = field(default_factory=document)
    home_vnum: str = ""
    egress_vnum: str = "3001"
    recall_vnum: str = "3001"
    char_name: str = ""
    char_file: str = ""
    skills: dict[str, PlayerSkill] = field(default_factory=dict)
    buffs: list[str] = field(default_factory=list)
    # consumables: list[Consumable] = field(default_factory=list)
    target_heros: int = 0
    meditate: bool = False
    refresher: bool = False
    true_seeing: bool = False
    valmeyjar: bool = False
    casting_speed: int = 0

    harvesting: PlayerHarvesting = field(default_factory=PlayerHarvesting)
    meta_gold_cost: Dict[str, int] = field(default_factory=dict)
    meta_xp_cost: Dict[str, int] = field(default_factory=dict)
    meta_exp_per_hero: Dict[str, float] = field(default_factory=dict)

    def save(self):
        # convert our convenience stuff back into the _config
        self.save_harvesting()
        self.save_meta()

        # write to disk
        with open(self.char_file, "w", encoding="UTF-8") as fp:
            fp.write(self._config.as_string())

    def load(self, data_dir: str, name: str):
        """Load a player character record from disk"""
        self.char_name = name.lower()

        char_file = os.path.join(data_dir, self.char_name)
        char_file = f"{char_file}.player"
        self.char_file = char_file
        if not os.path.isfile(self.char_file):
            with open(char_file, "w", encoding="UTF-8") as fp:
                fp.write(f"char_name = '{self.char_name}'\n")

        self._config = parse(open(char_file, "r", encoding="UTF-8").read())
        for key, val in self._config.items():
            if hasattr(self, key):
                setattr(self, key, val)

        # populating harvesting record
        self.parse_harvesting()

    def parse_harvesting(self):
        """Pull harvesting settings out of config"""
        harvest_conf = self._config.get("harvesting", {})
        for skill in fields(PlayerHarvesting):
            setattr(self.harvesting, skill.name, harvest_conf.get(skill.name, False))

    def save_harvesting(self):
        """Put harvesting settings into config"""
        harvesting = table()
        for skill in fields(PlayerHarvesting):
            harvesting[skill.name] = getattr(self.harvesting, skill.name, False)

        self._config["harvesting"] = harvesting

    def save_meta(self):
        self._config["meta_gold_cost"] = self.meta_gold_cost
        self._config["meta_xp_cost"] = self.meta_xp_cost
        self._config["meta_exp_per_hero"] = self.meta_exp_per_hero
