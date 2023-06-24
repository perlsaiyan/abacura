# from atlas.known_areas import KnownMob
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Encounter:
    name: str = ""
    ranged: bool = False
    paralyzed: bool = False
    alert: bool = False
    # known_mob: Optional[KnownMob] = None
    fighting: bool = False
    flags: List[str] = field(default_factory=List)
