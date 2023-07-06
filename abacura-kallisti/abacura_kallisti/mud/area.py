from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict, Tuple
from .mob import Mob
from functools import lru_cache


@dataclass()
class Area:
    name: str = ""
    include_areas: Optional[List] = field(default_factory=list)
    route: str = 'LRV'
    room_range: str = ''
    room_min_level: Dict[str, int] = field(default_factory=dict)
    room_max_level: Dict[str, int] = field(default_factory=dict)
    rooms_to_scout: Set[str] = field(default_factory=set)
    room_exclude: Set[str] = field(default_factory=set)
    exits_exclude: List[tuple] = field(default_factory=list)
    open_doors: bool = False
    enter_portals: bool = False
    track_random_portals: bool = False
    butcher: bool = False
    greedy_match: bool = False
    attacking_mobs: bool = False
    colorized_mobs: bool = False
    mobs: List[Mob] = field(default_factory=list)

    def __post_init__(self):
        # add the cache here to ensure it is an instance level cache
        self.get_excluded_room_vnums = lru_cache(100)(self.get_excluded_room_vnums)
        self.is_allowed_vnum = lru_cache(100)(self.is_allowed_vnum)

    def get_excluded_room_vnums(self, char_level: int) -> Set[str]:
        exclude = self.room_exclude.copy()
        min_lvl_exclude = {vnum for vnum, min_lvl in self.room_min_level.items() if char_level < min_lvl}
        max_lvl_exclude = {vnum for vnum, max_lvl in self.room_max_level.items() if char_level > max_lvl}
        exclude.update(min_lvl_exclude)
        exclude.update(max_lvl_exclude)

        # print('Exclude rooms %s ' % exclude)
        return exclude

    def get_allowed_ranges(self) -> List[Tuple[str]]:
        ranges = [tuple(r.split("-")) for r in self.room_range.split(",")]
        return ranges

    def is_allowed_vnum(self, vnum: str, char_level: int) -> bool:
        if vnum in ['L', 'C', '?', ''] or not vnum.isnumeric():
            return False

        ranges = self.get_allowed_ranges()
        in_range = any(int(rmin) <= int(vnum) <= int(rmax) for rmin, rmax in ranges)

        avoid = vnum in self.get_excluded_room_vnums(char_level)

        return in_range and not avoid

    def is_allowed_area(self, area_name) -> bool:
        return area_name in [self.name] + self.include_areas
