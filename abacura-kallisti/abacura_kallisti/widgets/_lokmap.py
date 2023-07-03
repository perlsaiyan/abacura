"""Kallisti Map Widget"""
from __future__ import annotations

from itertools import groupby
from rich.color import Color, ColorType
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from typing import TYPE_CHECKING, Optional, Tuple

from textual import log
from textual.app import ComposeResult
from textual.events import Resize
from textual.containers import Container, Center, Middle
from textual.widget import Widget
from textual.widgets import Static
from dataclasses import dataclass

from functools import lru_cache

from abacura.plugins.events import event
from abacura.mud.options.msdp import MSDPMessage
from abacura.widgets.resizehandle import ResizeHandle

if TYPE_CHECKING:
    from abacura.mud.session import Session
    from abacura_kallisti.atlas.world import World

class LOKMapBlock:
    terrains = {
        'Inside': Color("Inside", ColorType(3), None, ColorTriplet(75,74,75)),
        'City': Color("City", ColorType(3), None, ColorTriplet(40,42,46)),        
        'Field': Color("Field", ColorType(3), None, ColorTriplet(91,163,88)),
        'Forest': Color("Forest", ColorType(3), None, ColorTriplet(28,93,25)),
        'Path': Color("Path", ColorType(3), None, ColorTriplet(92,49,20)),
        'Hills': Color("Hills", ColorType(3), None, ColorTriplet(121,163,88)),
        'Mountains': Color("Mountains", ColorType(3), None, ColorTriplet(59,38,4)),
        'Water': Color("Water", ColorType(3), None, ColorTriplet(52,124,186)),
        'Deep': Color("Deep", ColorType(3), None, ColorTriplet(52, 124,240)),
        'Air': Color("Air", ColorType(3), None, ColorTriplet(177, 177,177)),
        'Underwater': Color("Underwater", ColorType(3), None, ColorTriplet(22,94,156)),              
        'Jungle': Color("Jungle", ColorType(3), None, ColorTriplet(28,143,25)),
        'Desert': Color("Desert", ColorType(3), None, ColorTriplet(243,203,147)),
        'Arctic': Color("Arctic", ColorType(3), None, ColorTriplet(200,200,214)),
        'Underground': Color("Underground", ColorType(3), None, ColorTriplet(55,55,55)),
        'Swamp': Color("Swamp", ColorType(3), None, ColorTriplet(55,85,85)),        
        'Ocean': Color("Ocean", ColorType(3), None, ColorTriplet(52, 104,250)),
        'Bridge': Color("Bridge", ColorType(3), None, ColorTriplet(122,79,50)),
        'Peak': Color("Peak", ColorType(3), None, ColorTriplet(201,195,185)),
        'Pasture': Color("Pasture", ColorType(3), None, ColorTriplet(91,163,88)),
        'Fence': Color("Fence", ColorType(3), None, ColorTriplet(255,255,255)),
        'Portal': Color("Portal", ColorType(3), None, ColorTriplet(255,255,255)),
        'ForestJungle': Color("ForestJungle", ColorType(3), None, ColorTriplet(28,93,25)),
        'Beach': Color("Beach", ColorType(3), None, ColorTriplet(238,223,147)),
        'Astral': Color("Astral", ColorType(3), None, ColorTriplet(177, 177,177)),
        'Planar': Color("Planar", ColorType(3), None, ColorTriplet(177, 177,177)),
        'Lava': Color("Lava", ColorType(3), None, ColorTriplet(255,0,0)),
        'Nothingness': Color("Nothingness", ColorType(3), None, ColorTriplet(255,255,255)),
        'Stairs': Color("Stairs", ColorType(3), None, ColorTriplet(255,255,255)),
        'Ice': Color("Ice", ColorType(3), None, ColorTriplet(255,255,255)),
        'Snow': Color("Snow", ColorType(3), None, ColorTriplet(230,230,250)),
        'Shallow': Color("Shallow", ColorType(3), None, ColorTriplet(90,164,228)),
        'Tundra': Color("Tundra", ColorType(3), None, ColorTriplet(220,220,220)),
    }

    def __init__(self, world: Optional[World], start_room, height, width):
        self.start_room = start_room
        self.world = world
        self.width = width
        self.height = height

    @lru_cache(maxsize=1000)
    def get_terrain2_icon(self, terrain: str) -> Color:
        """Return terrain color/icon"""
        return self.terrains.get(terrain.split()[0], Color("", ColorType(3), None, ColorTriplet(255,255,255)))

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        if self.width == 0 or self.height == 0:
            return
        BFS = []

        cenH = int(self.height/2)
        cenW = int(self.width/2)

        # Y is first in the matrix!
        blank = Color("", ColorType(3), None, ColorTriplet(0,0,0))
        Matrix = [[blank for x in range(self.width)] for y in range(self.height)]
        try:
            room = self.world.rooms[self.start_room]
        except KeyError:
            return
        visited = {}

        BFS.append(MapPoint(room.vnum, cenW, cenH))

        while len(BFS) > 0:
            here = BFS.pop(0)

            if here.room == '' or not here.room in self.world.rooms:
                continue

            if here.room in visited:
                continue
            visited[here.room] = 1

            room = self.world.rooms[here.room]
            room_exits = room.exits  # get this once to improve wilderness performance
                
            if Matrix[here.y][here.x] == blank:
                if room.vnum == self.start_room:
                    me_box = self.get_terrain2_icon(room.terrain_name)
                    Matrix[here.y][here.x] = Color("me",ColorType(3),None, me_box.triplet)
                else:
                    Matrix[here.y][here.x] = self.get_terrain2_icon(room.terrain_name)

                # Add exits to BFS
                if (here.y-1) >= 0 and "north" in room_exits:
                    if not room_exits["north"].to_vnum in visited:
                        #log(f"appending {room_exits['north']}")
                        BFS.append(MapPoint(room_exits["north"].to_vnum, here.x, here.y -1))
                if (here.y +1) < len(Matrix) and "south" in room_exits:
                    if not room_exits["south"].to_vnum in visited:
                        #log(f"appending {room_exits['south']}")
                        BFS.append(MapPoint(room_exits["south"].to_vnum, here.x, here.y+1))
                if (here.x +1) < len(Matrix[here.y]) and "east" in room_exits:
                    if not room_exits["east"].to_vnum in visited:
                        #log(f"appending {room_exits['east']}")
                        BFS.append(MapPoint(room_exits["east"].to_vnum, here.x+1, here.y))
                if (here.x -1) >= 0 and "west" in room_exits:
                    if not room_exits["west"].to_vnum in visited:
                        #log(f"appending {room_exits['west']}")
                        BFS.append(MapPoint(room_exits["west"].to_vnum, here.x-1, here.y))        

        @lru_cache(1000)
        def get_style(bgcolor):
            return Style(bgcolor=bgcolor)

        for row in Matrix:
            for color, n in [(color, len(list(g))) for color, g in groupby(row)]:
                if color.name == "me":
                    yield Segment("@", Style(color="red", bgcolor=color))
                else:
                    yield Segment(" " * n, get_style(bgcolor=color))
            yield Segment("\n")


@dataclass(slots=True, frozen=True)
class MapPoint:
    """Class to hold a room vnum and its location in our rooms matrix"""
    room: str
    x: int
    y: int


class LOKMap(Container):
    """Main map widget, used in sidebars and bigmap screen"""
    world: Optional[World] = None

    def __init__(self, resizer: bool=True, id: str=""):
        super().__init__()
        self.id=id
        self.resizer: bool = resizer
        self.map = Static(id="minimap", classes="lokmap", expand=True)
        self.START_ROOM = None

    def compose(self) -> ComposeResult:
        yield self.map
        if self.resizer:
            yield ResizeHandle(self, "bottom")

    def on_mount(self) -> None:
        # Register our listener until we have a RegisterableObject to descend from
        self.screen.session.listener(self.recenter_map)
        self.world = self.screen.world

    def generate_dense_map(self) -> None:
        if self.START_ROOM == "":
            log.warning("No start room present for map, do not draw")
            return
        BFS = []
       
        H = self.content_size.height - 1
        W = self.content_size.width
        cenH = int(H/2)
        cenW = int(W/2)

        # check if we're in a bad resize state and bail out
        if H == 0 or W == 0:
            return

        # Y is first in the matrix!
        Matrix = [[' ' for x in range(W)] for y in range(H)]
        try:
            room = self.world.rooms[self.START_ROOM]
        except KeyError:
            return
        visited = {}

        BFS.append(MapPoint(room.vnum, cenW-1, cenH))

        #while we've got rooms, iterate them
        while len(BFS) > 0:
            here = BFS.pop(0)
            if here.room == '' or not here.room in self.world.rooms:
                continue

            visited[here.room] = 1
            room = self.world.rooms[here.room]
            room_exits = room.exits  # get this once to improve wilderness performance
            if Matrix[here.y][here.x] == ' ':
                if room.vnum == self.START_ROOM:
                    Matrix[here.y][here.x] = "@"
                else:
                    Matrix[here.y][here.x] = self.get_terrain2_icon(room.terrain_name)

                # Add exits to BFS
                if (here.y-1) >= 0 and "north" in room_exits:
                    if not room_exits["north"].to_vnum in visited:
                        log(f"appending {room_exits['north']}")
                        BFS.append(MapPoint(room_exits["north"].to_vnum, here.x, here.y -1))

                if (here.y +1) < len(Matrix) and "south" in room_exits:
                    if not room_exits["south"].to_vnum in visited:
                        log(f"appending {room_exits['south']}")
                        BFS.append(MapPoint(room_exits["south"].to_vnum, here.x, here.y+1))

                if (here.x +1) < len(Matrix[here.y]) and "east" in room_exits:
                    if not room_exits["east"].to_vnum in visited:
                        log(f"appending {room_exits['east']}")
                        BFS.append(MapPoint(room_exits["east"].to_vnum, here.x+1, here.y))

                if (here.x -1) >= 0 and "west" in room_exits:
                    if not room_exits["west"].to_vnum in visited:
                        log(f"appending {room_exits['west']}")
                        BFS.append(MapPoint(room_exits["west"].to_vnum, here.x-1, here.y))        

        # draw the map with Matrix
        log(f"Matrix: {Matrix}")
        buf = "\n".join([''.join(yp) for yp in Matrix])
        self.map.update(Text.from_ansi(buf))

    def generate_map(self) -> None:
        #START_ROOM='3001'
        # Bail if we don't have a start room
        if self.START_ROOM == "":
            log.warning("No start room present for map, do not draw")
            return
        BFS = []
       
        H = self.content_size.height - 1
        W = self.content_size.width
        cH = int(H/3)
        cW = int(W/5)
        cenH = int(cH/2)
        cenW = int(cW/2)

        # check if we're in a bad resize state and bail out
        if cW == 0 or cH == 0:
            return

        # Y is first in the matrix!
        Matrix = [['' for x in range(cW)] for y in range(cH)]
        try:
            room = self.world.rooms[self.START_ROOM]
        except KeyError:
            return
        visited = {}

        BFS.append(MapPoint(room.vnum, cenW-1, cenH))

        #while we've got rooms, iterate them
        while len(BFS) > 0:
            here = BFS.pop(0)
            if here.room == '' or not here.room in self.world.rooms:
                continue

            visited[here.room] = 1
            room = self.world.rooms[here.room]
            room_exits = room.exits  # get this once to improve wilderness performance
            if Matrix[here.y][here.x] == '':
                Matrix[here.y][here.x] = here.room

                # Add exits to BFS
                if (here.y-1) >= 0 and "north" in room_exits:
                    if not room.exits["north"].to_vnum in visited:
                        log(f"appending {room_exits['north']}")
                        BFS.append(MapPoint(room_exits["north"].to_vnum, here.x, here.y -1))

                if (here.y +1) < len(Matrix) and "south" in room_exits:
                    if not room_exits["south"].to_vnum in visited:
                        log(f"appending {room_exits['south']}")
                        BFS.append(MapPoint(room_exits["south"].to_vnum, here.x, here.y+1))

                if (here.x +1) < len(Matrix[here.y]) and "east" in room_exits:
                    if not room_exits["east"].to_vnum in visited:
                        log(f"appending {room_exits['east']}")
                        BFS.append(MapPoint(room_exits["east"].to_vnum, here.x+1, here.y))

                if (here.x -1) >= 0 and "west" in room_exits:
                    if not room_exits["west"].to_vnum in visited:
                        log(f"appending {room_exits['west']}")
                        BFS.append(MapPoint(room_exits["west"].to_vnum, here.x-1, here.y))        

        # draw the map with Matrix of size Viewport
        buf = self.draw_map(Matrix, self.content_size.width, self.content_size.height-1)
        self.map.update(buf)

    def get_terrain2_icon(self, terrain: str) -> str:
        """Return terrain color/icon"""
        log(f"TERRAIN: {terrain}")
        if 'Inside' in terrain:
            return "\x1b[48;2;55;59;65m \x1b[0m"
        if 'Beach' in terrain:
            return "\x1b[48;2;238;207;147m \x1b[0m"
        if 'City' in terrain:
            return "\x1b[48;2;40;42;46m \x1b[0m"
        if 'Path' in terrain:
            return "\x1b[48;2;92;49;20m \x1b[0m"
        if 'Forest' in terrain:
            return "\x1b[48;2;28;93;25m \x1b[0m"
        if 'Field' in terrain:
            return "\x1b[48;2;91;163;88m \x1b[0m"
        if 'Desert' in terrain:
            return "\x1b[48;2;243;203;147m \x1b[0m"
        if 'Shallow Water' in terrain:
            return "\x1b[48;2;90;164;228m \x1b[0m"
        if 'Water' in terrain:
            return "\x1b[48;2;52;124;186m \x1b[0m"

        return " "


    def get_terrain_icon(self, terrain: str) -> str:
        """Return terrain color/icon"""
        if 'Inside' in terrain:
            return "[on rgb(55,59,65)] [/on rgb(55,59,65)]"
        if 'Beach' in terrain:
            return "[on rgb(238,207,147)] [/on rgb(238,207,147)]"
        if 'City' in terrain:
            return "[on rgb(40,42,46)] [/on rgb(40,42,46)]"
        if 'Path' in terrain:
            return "[on rgb(92,49,20)] [/on rgb(92,49,20)]"
        if 'Forest' in terrain:
            return "[on rgb(28,93,25)] [/on rgb(28,93,25)]"
        if 'Field' in terrain:
            return "[on rgb(91,163,88)] [/on rgb(91,163,88)]"
        if 'Desert' in terrain:
            return "[on rgb(243,203,147)] [/on rgb(243,203,147)]"
        if 'Shallow Water' in terrain:
            return "[on rgb(90,164,228)] [/on rgb(90,164,228)]"
        if 'Water' in terrain:
            return "[on rgb(52,124,186)] [/on rgb(52,124,186)]"
        
        return " "
        
    def draw_map(self, Matrix, cW, cH) -> str:
        xtmp = int((cW - len(Matrix[0])*5)/ 2)
        
        a_map = [[' ' for x in range(cW)] for y in range(cH)]
        # subtract one for the 0-index array
        y = 2 - 1

        for yp in Matrix:
            x = xtmp + 3 -1
            for xp in yp:
                if xp == '':
                    x += 5
                    continue
                    
                room = self.world.rooms[xp]
                t_icon = self.get_terrain_icon(room.terrain_name)
                if room.vnum == self.START_ROOM:
                    a_map[y][x] = "[bold red]@[/bold red]"
                
                a_map[y-1][x-1] = t_icon
                a_map[y-1][x-2] = t_icon
                a_map[y-1][x+2] = t_icon

                a_map[y][x-1] = "["
                a_map[y][x+1] = "]"

                a_map[y+1][x-1] = t_icon
                a_map[y+1][x-2] = t_icon
                a_map[y+1][x+2] = t_icon

                if "north" in room.exits:
                    a_map[y-1][x] = "|"
                else :
                    a_map[y-1][x] = t_icon
                if "south" in room.exits:
                    a_map[y+1][x] = "|"
                else :
                    a_map[y+1][x] = t_icon
                if "east" in room.exits:
                    a_map[y][x+2] = "—"
                else :
                    a_map[y][x+2] = t_icon
                if "west" in room.exits:
                    a_map[y][x-2] = "—"
                else :
                    a_map[y][x-2] = t_icon
                if "up" in room.exits:
                    a_map[y-1][x+1] = "+"
                else:
                    a_map[y-1][x+1] = t_icon
                if "down" in room.exits:
                    a_map[y+1][x+1] = "-"
                else :
                    a_map[y+1][x+1] = t_icon
                x += 5
            y += 3

        return "\n".join([''.join(yp) for yp in a_map])

    def on_resize(self, event: Resize):
        #self.generate_map()
        self.map.update(LOKMapBlock(self.world, self.START_ROOM, self.content_size.height, self.content_size.width))

    @event("msdp_value_ROOM_VNUM")
    def recenter_map(self, message: MSDPMessage):
        """Event to trigger map redraws on movement"""
        self.START_ROOM = str(message.value)
        #self.generate_dense_map()

        LMB = LOKMapBlock(self.world, self.START_ROOM, self.content_size.height, self.content_size.width)
        self.map.update(LMB)
        