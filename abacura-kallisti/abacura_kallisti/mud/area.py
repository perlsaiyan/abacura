from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict
from .mob import Mob


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
