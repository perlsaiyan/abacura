from abacura.plugins.events import AbacuraMessage
from dataclasses import dataclass
from .room import Room
from .world import World

from typing import Optional


@dataclass
class MapUpdateMessage(AbacuraMessage):
    start_room: Optional[Room] = None
    current_vnum: str = ''
    world: Optional[World] = None
    traveling: bool = False
    wilderness: bool = False
    ship: bool = False
    event_type: str = "lok.map.update"


@dataclass
class MapUpdateRequest(AbacuraMessage):
    event_type: str = "lok.map.update_request"
