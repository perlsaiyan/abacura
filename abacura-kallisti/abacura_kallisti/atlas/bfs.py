from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .room import Room
    from .world import World

@dataclass(slots=True, frozen=True)
class MapPoint:
    """Class to hold a room vnum and its location in our rooms matrix"""
    room: str
    x: int
    y: int

class BFS:
    """Breadth-First Search class"""
    def __init__(self, world: World):
        self.world: World = world

    def get_bfs_grid(self, start_room: Room, width: int = 0, height: int = 0, overscan: int = 0) -> List[List[Room|None]]:
        """Return Rooms in Grid around start room"""
        cen_h = int(height/2)
        cen_w = int(width/2)
        matrix = [[None for x in range(width + overscan)] for y in range(height + overscan)]

        if height <= 0 or width <= 0:
            return matrix # type: ignore[reportGeneralTypeIssues] for Pylance

        queue = []
        visited = {}
        queue.append(MapPoint(start_room.vnum, cen_w, cen_h))

        while len(queue) > 0:
            here = queue.pop(0)
            if here.room in visited or not here.room in self.world.rooms:
                continue
            visited[here.room] = 1
            room = self.world.rooms[here.room]
            room_exits = room.exits  # get this once to improve wilderness performance
            if matrix[here.y][here.x] is None:
                matrix[here.y][here.x] = room
                # Add exits to BFS
                if (here.y-1) >= 0 and "north" in room_exits:
                    if not room_exits["north"].to_vnum in visited:
                        queue.append(MapPoint(room_exits["north"].to_vnum, here.x, here.y -1))
                if (here.y +1) < len(matrix) and "south" in room_exits:
                    if not room_exits["south"].to_vnum in visited:
                        queue.append(MapPoint(room_exits["south"].to_vnum, here.x, here.y+1))
                if (here.x +1) < len(matrix[here.y]) and "east" in room_exits:
                    if not room_exits["east"].to_vnum in visited:
                        queue.append(MapPoint(room_exits["east"].to_vnum, here.x+1, here.y))
                if (here.x -1) >= 0 and "west" in room_exits:
                    if not room_exits["west"].to_vnum in visited:
                        queue.append(MapPoint(room_exits["west"].to_vnum, here.x-1, here.y))
        return matrix # type: ignore[reportGeneralTypeIssues] Pylance hates this one weird trick
