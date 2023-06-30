from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from . import encounter
from . import item
from .terrain import TERRAIN, Terrain

from abacura.plugins.events import AbacuraMessage


@dataclass
class ScannedRoom:
    room_vnum: str = ''
    room_header: str = ''
    room_items: List[item.Item] = field(default_factory=list)
    room_corpses: List[str] = field(default_factory=list)
    room_encounters: List[encounter.Encounter] = field(default_factory=list)
    room_charmies: List[str] = field(default_factory=list)
    room_players: List[str] = field(default_factory=list)
    room_lines: List[str] = field(default_factory=list)
    blood_trail: str = ''
    hunt_tracks: str = ''
    # minimap: List[str] = field(default_factory=list)

    # def get_hash(self):
    #     header = self.room_header
    #     for c in "[]()|":
    #         header = header.replace(c, "")
    #     # TODO: strip out hidden exits that appear sometimes instead of just stripping the () characters
    #     return hash(self.room_vnum + "\n" + self.room_header + "\n".join(self.minimap))


class RoomMessage(AbacuraMessage):
    """Message when a room is viewed"""
    def __init__(self, vnum: str, scanned_room: ScannedRoom):
        super().__init__(vnum, scanned_room)
        self.vnum = vnum
        self.room: ScannedRoom = scanned_room


@dataclass(slots=True)
class Exit:
    from_vnum: str = ''
    direction: str = ''
    to_vnum: str = ''
    portal: str = ''
    portal_method: str = ''
    door: str = ''
    closes: bool = False
    locks: bool = False
    key_name: str = ''
    weight: int = 0
    max_level: int = 100
    min_level: int = 0
    deathtrap: bool = False


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
    navigable: bool = True
    # exits should be last to make the simple db query work
    exits: Dict[str, Exit] = field(default_factory=dict)

    @property
    def terrain(self) -> Terrain:
        return TERRAIN[self.terrain_name]


@dataclass(slots=True)
class RoomTracking:
    vnum: str = ""
    last_harvested: Optional[datetime] = None
    last_visited: Optional[datetime] = None
    last_searched: Optional[datetime] = None
    kills: int = 0
