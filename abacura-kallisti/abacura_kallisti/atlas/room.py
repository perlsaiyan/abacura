from dataclasses import dataclass, field
from typing import List

from . import encounter


# @dataclass(slots=True)
@dataclass
class ScannedRoom:
    room_vnum: str = ''
    room_header: str = ''
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
