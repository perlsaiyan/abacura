"""
LOK Map Widget
"""

from typing import Optional

from rich.color import Color, ColorType
from rich.color_triplet import ColorTriplet
from rich.segment import Segment
from rich.style import Style
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Resize
from textual.strip import Strip
from textual.widgets import Static

from abacura.mud.options.msdp import MSDPMessage, MSDP
from abacura.plugins.events import event
from abacura.widgets.resizehandle import ResizeHandle
from abacura_kallisti.atlas.bfs import BFS
from abacura_kallisti.atlas.room import Room
from abacura_kallisti.atlas.world import World
from abacura_kallisti.plugins.scripts.travel import TravelStatus


class LOKMapStatic(Static):
    def __init__(self, strips: list[Strip], **kwargs):
        super().__init__(**kwargs)
        self.strips = strips

    def get_content_height(self, container, viewport, width) -> int:
        log.warning(f"Content size {len(self.strips)}")
        return len(self.strips)

    def render_line(self, y: int) -> Strip:
        if y < len(self.strips):
            return self.strips[y]
        else:
            return Strip([])

    def refresh_strips(self, strips: list[Strip]):
        self.strips = strips
        self.refresh()


class LOKMap(Container):
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

    def __init__(self, resizer: bool=True, id: str = ""):
        super().__init__()
        self.id = id
        self.resizer: bool = resizer
        self.strips: list = []
        self.world: Optional[World] = None
        self.map_type: str = "5x3"
        self.start_room: Optional[Room] = None
        self.bfs: Optional[BFS] = None
        self.msdp: Optional[MSDP] = None
        self.map = LOKMapStatic(self.strips, id = "minimap", classes="lokmap")


    def compose(self) -> ComposeResult:
        yield self.map
        if self.resizer:
            yield ResizeHandle(self, "bottom")

    def on_mount(self) -> None:
        # Register our listener until we have a RegisterableObject to descend from
        self.screen.session.add_listener(self.recenter_map)
        self.screen.session.add_listener(self.toggle_map_type)
        self.world = self.screen.session.additional_plugin_context['world']
        self.bfs = BFS(self.world)
        self.msdp = self.screen.session.core_msdp

    def on_resize(self, _event: Resize):
        self.update_map()
    
    @event("lok.travel.status")
    def toggle_map_type(self, status: TravelStatus):
        if status.steps_remaining > 0:
            self.map_type = "1x1"
            return
        
        self.map_type = "5x3"
        self.update_map()

    @event("core.msdp.ROOM_VNUM")
    def recenter_map(self, message: MSDPMessage):
        """Event to trigger map redraws on movement"""
        if self.world is None:
            return
        self.start_room = self.world.rooms.get(message.value, None)
        self.update_map()

    def update_map(self):
        if self.start_room is None:
            return
        width = self.content_size.width - 1
        height = self.content_size.height

        if self.map_type == "5x3":
            self.generate_5x3_map(self.start_room, width, height)
        if self.map_type == "1x1":
            self.generate_1x1_map(self.start_room, width, height)

        self.map.refresh_strips(self.strips)

    def color_for_terrain(self, terrain: str):
        return self.terrains.get(terrain.split(" ")[0], Color("empty", ColorType(3), None, ColorTriplet(0,0,0)))

    def make_5x3_top_row(self, room: Optional[Room]) -> list[Segment]:
        if room is None:
            return [Segment("     ")]
        color = self.color_for_terrain(room.terrain_name)
        segments = [Segment("  ", Style(bgcolor=color))]
        segments.append(Segment("|" if "north" in room.exits else " ", Style(bgcolor=color)))
        segments.append(Segment("+ " if "up" in room.exits else "  ", Style(bgcolor=color)))
        return segments

    def make_5x3_mid_row(self, room: Optional[Room]) -> list[Segment]:
        if room is None:
            return [Segment("     ")]
        color = self.color_for_terrain(room.terrain_name)
        segments = [Segment("-[" if "west" in room.exits else " [", Style(bgcolor=color))]
        segments.append(Segment("@" if room.vnum == self.msdp.values["ROOM_VNUM"] else " ", Style(color="red", bgcolor=color)))
        segments.append(Segment("]-" if "east" in room.exits else "] ", Style(bgcolor=color)))
        return segments

    def make_5x3_bot_row(self, room: Optional[Room]) -> list[Segment]:
        if room is None:
            return [Segment("     ")]
        color = self.color_for_terrain(room.terrain_name)
        segments = [Segment("  ", Style(bgcolor=color))]
        segments.append(Segment("|" if "south" in room.exits else " ", Style(bgcolor=color)))
        segments.append(Segment("- " if "down" in room.exits else "  ", Style(bgcolor=color)))
        return segments

    def generate_5x3_map(self, start_room: Room, width, height):
        if self.bfs is None:
            return
        
        g_width = int(width / 5) 
        g_height = int(height / 3) 

        grid = self.bfs.get_bfs_grid(start_room, g_width, g_height, overscan=2)

        self.strips = []
        for row in grid:
            # doing three rows at a time
            row1 = []
            row2 = []
            row3 = []
            for cell in row:
                # For each cell, make a Segment, append to three rows
                row1.extend(self.make_5x3_top_row(cell))
                row2.extend(self.make_5x3_mid_row(cell))
                row3.extend(self.make_5x3_bot_row(cell))

            self.strips.append(Strip(row1))
            self.strips.append(Strip(row2))
            self.strips.append(Strip(row3))

    def generate_1x1_map(self, start_room: Room, width, height):
        if self.bfs is None:
            return
        
        grid = self.bfs.get_bfs_grid(start_room, width, height)

        self.strips = []
        for line in grid:
            row = []
            for cell in line:
                if cell is None:
                    row.append(Segment(" ", Style(bgcolor="black")))
                    continue
                color = self.color_for_terrain(cell.terrain_name)
                if cell.vnum == self.msdp.values["ROOM_VNUM"]:
                    row.append(Segment("@", Style(color="red", bgcolor=color)))
                else:
                    row.append(Segment(" ", Style(bgcolor=color)))
            self.strips.append(Strip(row))