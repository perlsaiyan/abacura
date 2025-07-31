from dataclasses import dataclass, field, fields
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional, Set
import re

from abacura.mud import OutputMessage
from abacura.plugins.events import AbacuraMessage
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.mud.area import Area
from abacura_kallisti.mud.mob import Mob
from .terrain import TERRAIN, Terrain


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
    max_level: int = 110
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

        if self.closes or self.door:
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


class ScannedMiniMap:
    def __init__(self, messages: List[OutputMessage] = None):
        self.you: Optional[tuple] = None
        self.grid: Dict[tuple, str] = {}
        self.messages: List[OutputMessage] = messages or []

        if messages is None:
            return

        for y, msg in enumerate(self.messages):
            for x, symbol in enumerate(msg.stripped):
                if symbol == '@':
                    self.you = (x, y)
                elif symbol != ' ':
                    self.grid[(x, y)] = symbol

        # recalculate points relative to the @ symbol
        if self.you is not None:
            self.grid = {(k[0] - self.you[0], k[1] - self.you[1]): v for k, v in self.grid.items()}

    def __repr__(self):
        return f"ScannedMiniMap({[m.stripped for m in self.messages]})"


@dataclass
class RoomHeader:
    line: str = field(repr=False, default='')
    name: str = ''
    exits: List[str] = field(default_factory=list)
    flags: Set[str] = field(default_factory=set)
    compass: bool = False
    terrain_name: str = ''
    time: str = ''
    weather: str = ''


@dataclass(repr=True)
class RoomPlayer:
    line: str = field(repr=False, default='')
    name: str = ''
    race: str = ''
    flags: Set[str] = field(default_factory=set)
    # evil sanc (same list as mobs)
    riding: str = ''


@dataclass
class RoomItem:
    line: str = field(repr=False, default='')
    description: str = ''
    short: str = ''
    quantity: int = 1
    blue: bool = False
    flags: Set[str] = field(default_factory=set)


@dataclass
class RoomCorpse:
    line: str = field(repr=False, default='')
    description: str = ''
    quantity: int = 1
    corpse_type: str = ''
    # related mob from atlas/area


@dataclass
class RoomMob(Mob):
    line: str = field(repr=False, default='')
    description: str = ''
    quantity: int = 1
    position: str = ''
    has_quest: bool = False
    alert: bool = False
    paralyzed: bool = False
    fighting: bool = False
    fighting_you: bool = False
    following_you: bool = False
    ranged: bool = False
    flags: Set[str] = field(default_factory=set)
    noattack: bool = False

    def copy_mob_properties(self, mob: Mob):
        for f in fields(Mob):
            setattr(self, f.name, getattr(mob, f.name))


@dataclass
class ScannedRoom(Room):
    header: RoomHeader = field(default_factory=RoomHeader)
    area: Area = field(default_factory=Area)
    items: List[RoomItem] = field(default_factory=list)
    corpses: List[RoomCorpse] = field(default_factory=list)
    mobs: List[RoomMob] = field(default_factory=list)
    players: List[RoomPlayer] = field(default_factory=list)
    minimap: ScannedMiniMap = field(default_factory=ScannedMiniMap)
    warded: bool = False
    blood_trail: str = ''
    hunt_tracks: str = ''
    msdp_exits: Dict[str, str] = field(default_factory=dict)

    def identify_room_mobs(self):
        if len(self.area.mobs) == 0:
            return

        for rm in self.mobs:
            for am in self.area.mobs:
                if am.starts_with != '' and re.match(f"^{am.starts_with}[, ]", rm.description):
                    rm.copy_mob_properties(am)
                    continue

                if f" {am.name} " in rm.description:
                    rm.copy_mob_properties(am)
                    continue


@dataclass
class RoomMessage(AbacuraMessage):
    """Message when a room is viewed"""
    vnum: str = ""
    room: ScannedRoom = None
    event_type: str = "lok.room"
