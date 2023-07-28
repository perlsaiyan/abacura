import importlib
from dataclasses import fields

from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

import abacura.utils.tabulate as tblt
from abacura.plugins import command, CommandError
from abacura.utils.tabulate import tabulate
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.atlas.world import Room, Exit
from abacura_kallisti.plugins import LOKPlugin


class AreaController(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.wild_grid = WildernessGrid()
        importlib.reload(tblt)
        self.traveling = False

    @command(name="visited")
    def show_visited_rooms_in_area(self, area: str = ''):
        """
        Show rooms in area and if they have been visited

        :param area: Optional area name, defaults to current area
        """
        if area == '':
            if self.msdp.room_vnum in self.world.rooms:
                area = self.world.rooms[self.msdp.room_vnum].area_name
            else:
                raise CommandError('Unknown area')
        else:
            areas = {r.area_name: True for r in self.world.rooms.values()}
            match_areas = [a for a in areas.keys() if a.lower().startswith(area.lower())]
            match_areas.sort(key=lambda a: 100 - abs(len(a) - len(area)))
            if len(match_areas) == 0:
                raise CommandError('Unknown area %s' % area)
            area = match_areas[0]

        rooms = [r for r in self.world.rooms.values() if r.area_name == area]

        sorted_rooms = list(sorted(rooms, key=lambda x: x.vnum))[:300]

        rows = []
        r: Room
        for r in sorted_rooms:
            e: Exit
            for e in r.exits.values():
                known: bool = e.to_vnum in self.world.rooms
                visited = known and self.world.rooms[e.to_vnum].last_visited

                rows.append([r.vnum, r.name, e.direction, e.to_vnum, bool(e.closes), bool(e.locks), known, visited])

        headers = ("_Room", "Name", "Direction", "_To Room", "Closes", "Locks", "Known", "Visited")
        table = tabulate(rows, headers=headers, caption=f"{len(sorted_rooms)} of {len(rooms)} rooms shown")
        self.session.output(table, actionable=False)

        num_visited = len([r for r in rooms if r.last_visited])
        num_rooms = len(rooms)
        self.session.output(f"\nArea:{area}\n\n  Known Rooms: {num_rooms:5d}\nVisited Rooms: {num_visited:5d}",
                            actionable=False)

    @command()
    def area(self):
        """
        View all known mobs in the current area
        """

        header_text = Text.assemble((f"Area ", "purple"), "[", (self.room.area.name, "bright cyan"), "]")

        properties = []
        for f in fields(self.room.area):
            if f.name == 'mobs':
                continue
            t = Text.assemble((f"{f.name:>15.15s}: ", "bold white"),
                              (str(getattr(self.room.area, f.name, '')), "white"))
            properties.append(t)

        # blood = Text.assemble((f"{'blood':>12.12s}: ", "bold white"), (self.room.blood_trail, "bold red"))
        # hunt = Text.assemble((f"{'tracks':>12.12s}: ", "bold white"), (self.room.hunt_tracks, "bold green"))

        properties_columns = Columns(properties, width=50)

        rows = []
        for mob in self.room.area.mobs:
            rows.append((mob.name, mob.starts_with, mob.attack_name, mob.level, mob.race, mob.cls))
        table = tabulate(rows, headers=["Name", "Starts With", "Attack Name", "Level", "Race", "Class"],
                         title="Known Area Mobs", title_justify="left")

        group = Group(header_text, Text(""), properties_columns, Text(""), table)
        panel = Panel(group, width=110)
        self.output(panel, highlight=True)

    @command(name="mob")
    def mob_command(self, n: int = -1):
        if n < 0:
            rows = []
            for i, m in enumerate(self.room.mobs):
                rows.append((i, m.name, m.level, m.description, m.race, m.cls, m.starts_with, m.attack_name))

            self.output(tabulate(rows, headers=("#", "Name", "Level", "Description",
                                                "Race", "Class", "Startswith", "Attack Name"),
                                 title="Scanned Mobs in Room", title_justify="left"))
            return

        if n > len(self.room.mobs):
            raise CommandError(f"Invalid mob # '{n}'")

        properties = []
        mob = self.room.mobs[n]
        for f in fields(mob):
            if f.name == 'line':
                continue
            properties.append((f.name, getattr(mob, f.name, '')))

        tbl = tabulate(properties, headers=("Property", "Value"), title="Mob Properties")
        self.output(tbl)
