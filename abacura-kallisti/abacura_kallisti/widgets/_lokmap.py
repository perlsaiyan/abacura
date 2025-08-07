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

from abacura.plugins.events import event
from abacura.widgets.resizehandle import ResizeHandle
from abacura_kallisti.atlas.messages import MapUpdateMessage, MapUpdateRequest
from abacura_kallisti.atlas.room import Room
from abacura_kallisti.atlas.bfs import BFS
from dataclasses import dataclass
from functools import lru_cache


@dataclass(eq=True, frozen=True, slots=True)
class TerrainStyle:
    name: str = ""
    symbol: str = " "
    color: ColorTriplet = ColorTriplet(0, 0, 0)
    bg_color: ColorTriplet = ColorTriplet(0, 0, 0)

    @property
    @lru_cache(256)
    def style(self) -> Style:
        fg = Color(f"fg-{id(self)}", ColorType(3), None, self.color)
        bg = Color(f"bg-{id(self)}", ColorType(3), None, self.bg_color)
        return Style(color=fg, bgcolor=bg)


TERRAINS: list[TerrainStyle] = [
    TerrainStyle(' ', " ", ColorTriplet(0, 0, 0), ColorTriplet(0, 0, 0)),
    TerrainStyle('Air', ".", ColorTriplet(100, 100, 100), ColorTriplet(177, 177, 177)),
    TerrainStyle('Arctic', "░", ColorTriplet(240, 240, 255), ColorTriplet(200, 200, 214)),
    TerrainStyle('Astral', ".", ColorTriplet(50, 50, 50), ColorTriplet(177, 177, 177)),
    TerrainStyle('Beach', "~", ColorTriplet(255, 239, 158), ColorTriplet(238, 223, 147)),
    TerrainStyle('Bridge', "=", ColorTriplet(230, 230, 230), ColorTriplet(122, 79, 50)),
    TerrainStyle('City', "+", ColorTriplet(200, 220, 200), ColorTriplet(40, 42, 46)),
    TerrainStyle('Desert', ".", ColorTriplet(143, 118, 84), ColorTriplet(243, 203, 147)),
    TerrainStyle('Fence', "|", ColorTriplet(50, 200, 50), ColorTriplet(255, 255, 255)),
    TerrainStyle('Field', ".", ColorTriplet(77, 142, 74), ColorTriplet(91, 163, 88)),
    TerrainStyle('Forest', "⊛", ColorTriplet(49, 163, 44), ColorTriplet(28, 93, 25)),
    TerrainStyle('ForestJungle', "◉", ColorTriplet(62, 204, 55), ColorTriplet(28, 93, 25)),
    TerrainStyle('Hills', "◠", ColorTriplet(78, 118, 10), ColorTriplet(121, 163, 88)),  # ⏜◠˰◚ₙ≏
    TerrainStyle('Ice', "▒", ColorTriplet(200, 200, 220), ColorTriplet(240, 240, 255)),
    TerrainStyle('Inside', "o", ColorTriplet(220, 200, 200), ColorTriplet(75, 74, 75)),
    TerrainStyle('Jungle', "◉", ColorTriplet(45, 237, 30), ColorTriplet(28, 143, 25)),
    TerrainStyle('Lava', "≈", ColorTriplet(212, 91, 4), ColorTriplet(200, 0, 0)),
    TerrainStyle('Lush', 'x', ColorTriplet(45, 255, 30), ColorTriplet(28, 143, 25)),
    TerrainStyle('Mountains', "◭", ColorTriplet(59, 38, 4),  ColorTriplet(121, 110, 91)), # ColorTriplet(200, 190, 190) ColorTriplet(59, 38, 4)),  # ◣▴^  △ΔΛΛ▲⏶▴◭
    TerrainStyle('Nothingness', ".", ColorTriplet(220, 220, 220), ColorTriplet(255, 255, 255)),
    TerrainStyle('Pasture', ".", ColorTriplet(198, 207, 105), ColorTriplet(91, 163, 88)),
    TerrainStyle('Path', "-", ColorTriplet(133, 126, 122), ColorTriplet(92, 49, 20)),
    TerrainStyle('Peak', "^", ColorTriplet(245, 250, 255), ColorTriplet(101, 90, 71)),  # ColorTriplet(201, 195, 185)),
    TerrainStyle('Planar', ".", ColorTriplet(60, 60, 60), ColorTriplet(177, 177, 177)),
    TerrainStyle('Portal', "&", ColorTriplet(150, 150, 150), ColorTriplet(255, 255, 255)),
    TerrainStyle('Snow', "❄", ColorTriplet(245, 250, 255), ColorTriplet(230, 230, 250)),
    TerrainStyle('Stairs', "▟", ColorTriplet(220, 200, 200), ColorTriplet(75, 74, 75)),  # ColorTriplet(255, 255, 255)),
    TerrainStyle('Swamp', "~", ColorTriplet(26, 61, 32), ColorTriplet(55, 95, 85)),
    TerrainStyle('Tundra', ".", ColorTriplet(245, 250, 255), ColorTriplet(220, 220, 220)),
    TerrainStyle('Underground', "o", ColorTriplet(160, 160, 160), ColorTriplet(55, 55, 55)),
    TerrainStyle('Underwater', "~", ColorTriplet(40, 146, 237), ColorTriplet(22, 94, 156)),
    TerrainStyle('Shallow', "~", ColorTriplet(95, 212, 245), ColorTriplet(90, 164, 228)),
    TerrainStyle('Water', "~", ColorTriplet(62, 134, 240), ColorTriplet(52, 124, 220)),
    TerrainStyle('Deep', "≃", ColorTriplet(82, 154, 255), ColorTriplet(42, 104, 210)),
    TerrainStyle('Ocean', "≅", ColorTriplet(102, 174, 255), ColorTriplet(26, 57, 125)),
]

TERRAIN_LOOKUP: dict[str, TerrainStyle] = {t.name: t for t in TERRAINS}


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

    def __init__(self, resizer: bool = True, id: str = "", map_type: str = "auto"):
        super().__init__()
        self.id = id
        self.resizer: bool = resizer
        self.strips: list = []
        self.map_type: str = map_type
        self.start_room: Optional[Room] = None
        self.bfs: Optional[BFS] = None
        self.current_vnum: str = ''
        self.traveling: bool = False
        self.wilderness: bool = False

        self.map = LOKMapStatic(self.strips, id="minimap", classes="lokmap")

    def is_mouse_over(self) -> bool:
        """Override to handle Textual 5.x compatibility issues with mouse position."""
        try:
            if not self.screen.is_active:
                return False
            for widget, _ in self.screen.get_widgets_at(*self.app.mouse_position):
                if widget is self:
                    return True
            return False
        except (IndexError, AttributeError):
            # Handle case where screen is not properly initialized or mouse position is invalid
            return False

    def compose(self) -> ComposeResult:
        yield self.map
        if self.resizer:
            yield ResizeHandle(self, "bottom")

    def on_mount(self) -> None:
        # Register our listener until we have a RegisterableObject to descend from
        self.screen.session.director.register_object(self)
        self.screen.session.dispatch(MapUpdateRequest())

    def unregister(self):
        self.screen.session.director.unregister_object(self)

    def on_resize(self, _event: Resize):
        self.update_map()

    @event(MapUpdateMessage.event_type)
    def process_map_update(self, message: MapUpdateMessage):
        """Event to trigger map redraws on movement"""

        self.start_room = message.start_room
        self.current_vnum = message.current_vnum
        if not self.bfs:
            self.bfs = BFS(message.world)
        self.traveling = message.traveling
        self.wilderness = message.wilderness
        self.update_map()

    def update_map(self):
        if self.start_room is None:
            return

        width = self.content_size.width - 1
        height = self.content_size.height

        map_type = self.map_type

        if self.wilderness:
            map_type = "wilderness"

        if map_type == "auto":
            map_type = '1x1' if self.traveling else '5x3'

        match map_type:
            case "5x3": self.generate_5x3_map(self.start_room, width, height)
            case "3x3": self.generate_3x3_map(self.start_room, width, height)
            case "1x1": self.generate_1x1_map(self.start_room, width, height)
            case "wilderness": self.generate_wilderness_map(self.start_room, width, height)

        self.map.refresh_strips(self.strips)

    @staticmethod
    def terrain_style_for_terrain(terrain: str) -> TerrainStyle:
        return TERRAIN_LOOKUP.get(terrain.split(" ")[0], TERRAIN_LOOKUP[" "])

    def make_5x3_top_row(self, room: Optional[Room]) -> list[Segment]:
        if room is None:
            return [Segment("     ")]
        style = self.terrain_style_for_terrain(room.terrain_name).style
        return [Segment("  ", Style(bgcolor=style.bgcolor)),
                Segment("|" if "north" in room.exits else " ", Style(bgcolor=style.bgcolor)),
                Segment("+ " if "up" in room.exits else "  ", Style(bgcolor=style.bgcolor))]

    def make_5x3_mid_row(self, room: Optional[Room]) -> list[Segment]:
        if room is None:
            return [Segment("     ")]
        style = self.terrain_style_for_terrain(room.terrain_name).style
        return [Segment("-[" if "west" in room.exits else " [", Style(bgcolor=style.bgcolor)),
                Segment("@" if room.vnum == self.current_vnum else " ", Style(color="red", bgcolor=style.bgcolor)),
                Segment("]-" if "east" in room.exits else "] ", Style(bgcolor=style.bgcolor))]

    def make_5x3_bot_row(self, room: Optional[Room]) -> list[Segment]:
        if room is None:
            return [Segment("     ")]
        style = self.terrain_style_for_terrain(room.terrain_name).style
        return [Segment("  ", Style(bgcolor=style.bgcolor)),
                Segment("|" if "south" in room.exits else " ", Style(bgcolor=style.bgcolor)),
                Segment("- " if "down" in room.exits else "  ", Style(bgcolor=style.bgcolor))]

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

    def make_3x3_segments(self, sub_row: int, room: Optional[Room]) -> list[Segment]:

        if room is None:
            return [Segment("   ")]
        bgcolor = self.terrain_style_for_terrain(room.terrain_name).style.bgcolor
        style = Style(color="gray66", bgcolor=bgcolor)
        c2_color = style.color

        symbols = {(True, True, True): "↕",  # ◆ ±
                   (True, True, False): "↑",  # ⬘
                   (True, False, True): "↓",  # ⬙
                   (True, False, False): "▮",  # ☻ ▣ █
                   (False, True, True): "↕",  # ◆
                   (False, True, False): "↑",  # ⬘ ▲
                   (False, False, True): "↓",  # ⬙ ▼
                   (False, False, False): "▯"  # ○ □
                   }

        c1 = c2 = c3 = " "
        match sub_row:
            case 0:
                if 'north' in room.exits:
                    c2 = "│" if not room.exits['north'].locks else "║"
            case 1:
                if 'west' in room.exits:
                    c1 = "─" if not room.exits['west'].locks else "═"

                if 'east' in room.exits:
                    c3 = "─" if not room.exits['east'].locks else "═"

                current = self.current_vnum == room.vnum
                up = 'up' in room.exits
                down = 'down' in room.exits

                if current:
                    c2_color = "red"
                elif up or down:
                    c2_color = "white"

                c2 = symbols[(current, up, down)]

            case 2:
                if 'south' in room.exits:
                    c2 = "│" if not room.exits['south'].locks else "║"

        if c2_color != style.color:
            return [Segment(c1, style),
                    Segment(c2, Style(bold=True, color=c2_color, bgcolor=bgcolor)),
                    Segment(c3, style)]

        return [Segment(f"{c1}{c2}{c3}", style)]

    def generate_3x3_map(self, start_room: Room, width, height):
        if self.bfs is None:
            return

        g_width = int(width / 3)
        g_height = int(height / 3)

        grid = self.bfs.get_bfs_grid(start_room, g_width, g_height, overscan=2)

        self.strips = []
        for row in grid:
            # doing three sub-rows at a time
            self.strips += [Strip([s for cell in row for s in self.make_3x3_segments(i, cell)]) for i in range(3)]

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
                bgcolor = self.terrain_style_for_terrain(cell.terrain_name).style.bgcolor
                if cell.vnum == self.current_vnum:
                    row.append(Segment("@", Style(color="red", bgcolor=bgcolor)))
                else:
                    row.append(Segment(" ", Style(bgcolor=bgcolor)))
            self.strips.append(Strip(row))

    def generate_wilderness_map(self, start_room: Room, width, height):
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

                terrain = self.terrain_style_for_terrain(cell.terrain_name)

                if cell.vnum == self.current_vnum:
                    row.append(Segment("@", Style(color="red", bgcolor=terrain.style.bgcolor)))
                else:
                    row.append(Segment(terrain.symbol, terrain.style))

            self.strips.append(Strip(row))
