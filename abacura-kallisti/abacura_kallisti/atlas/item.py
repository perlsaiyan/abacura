from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Item:
    name: str = ""
    blue: bool = False
    count: int = 0
    #flags: List[str] = field(default_factory=List)