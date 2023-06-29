from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Item:
    name: str = ""
    blue: bool = False
    #flags: List[str] = field(default_factory=List)