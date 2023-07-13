from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import List, Dict, Optional
from functools import lru_cache

from . import encounter
from . import item
from .terrain import TERRAIN, Terrain

from abacura.plugins.events import AbacuraMessage
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.mud.area import Area


@dataclass(slots=True)
class Exit:
    from_vnum: str = ''
    direction: str = ''
    to_vnum: str = ''
    door: str = ''
    closes: bool = False
    locks: bool = False
    key_name: str = ''
    weight: int = 0
    max_level: int = 100
    min_level: int = 0
    deathtrap: bool = False
    commands: str = ''
    _temporary: bool = False

    @classmethod
    @lru_cache()
    def persistent_fields(cls) -> List[str]:
        return [f.name for f in fields(cls) if not f.name.startswith("_")]

    @property
    def temporary(self) -> bool:
        return self._temporary

    def get_commands(self) -> List[str]:
        if self.commands:
            return self.commands.split(";")

        if self.closes:
            return [f"open {self.door or 'door'} {self.direction}", self.direction]

        if self.direction in ['home', 'depart', 'recall']:
            return [self.direction]

        return [self.direction[0]]


@dataclass(slots=True)
class Room:
    vnum: str = ""
    name: str = ""
    terrain_name: str = ""
    area_name: str = ""
    regen_hp: bool = False
    regen_mp: bool = False
    regen_sp: bool = False
    set_recall: bool = False
    peaceful: bool = False
    deathtrap: bool = False
    silent: bool = False
    wild_magic: bool = False
    bank: bool = False
    narrow: bool = False
    no_magic: bool = False
    no_recall: bool = False
    last_visited: Optional[datetime] = None
    last_harvested: Optional[datetime] = None
    # _exits should be last to make the simple db query work
    _exits: Dict[str, Exit] = field(default_factory=dict)

    @property
    def terrain(self) -> Terrain:
        return TERRAIN[self.terrain_name]

    @classmethod
    @lru_cache()
    def persistent_fields(cls) -> List[str]:
        return [f.name for f in fields(cls) if not f.name.startswith("_")]

    @staticmethod
    @lru_cache(maxsize=100000)
    def get_wilderness_temp_exits(vnum: str) -> Dict[str, Exit]:
        wilderness_exits = {}
        grid = WildernessGrid()
        for direction, to_vnum in grid.get_exits(vnum).items():
            e = Exit(direction=direction, from_vnum=vnum, to_vnum=to_vnum, _temporary=True)
            wilderness_exits[direction] = e

        return wilderness_exits

    @property
    def exits(self) -> Dict[str, Exit]:
        try:
            v = int(self.vnum)
        except ValueError:
            return self._exits

        if v < 70000:
            return self._exits

        result = self._exits.copy()
        result.update(self.get_wilderness_temp_exits(self.vnum))
        return result


@dataclass
class ScannedRoom(Room):
    area: Area = field(default_factory=Area)
    room_header: str = ''
    room_items: List[item.Item] = field(default_factory=list)
    room_corpses: List[str] = field(default_factory=list)
    room_encounters: List[encounter.Encounter] = field(default_factory=list)
    room_charmies: List[str] = field(default_factory=list)
    room_players: List[str] = field(default_factory=list)
    room_lines: List[str] = field(default_factory=list)
    blood_trail: str = ''
    hunt_tracks: str = ''
    msdp_exits: Dict[str, str] = field(default_factory=dict)
    # minimap: List[str] = field(default_factory=list)

    # def get_hash(self):
    #     header = self.room_header
    #     for c in "[]()|":
    #         header = header.replace(c, "")
    #     # TODO: strip out hidden exits that appear sometimes instead of just stripping the () characters
    #     return hash(self.room_vnum + "\n" + self.room_header + "\n".join(self.minimap))


@dataclass
class RoomMessage(AbacuraMessage):
    """Message when a room is viewed"""
    vnum: str = ""
    room: ScannedRoom = None
    event_type: str = "lok.room"
