import importlib
from dataclasses import fields

from rich.text import Text

import abacura.utils.renderables as tblt
from abacura.plugins import command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPropertyGroup, AbacuraPanel, Group
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.atlas.world import Room, Exit
from abacura_kallisti.plugins import LOKPlugin


class AreaController(LOKPlugin):
    """Commands for manipulating the database of areas and mobs"""
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

                rows.append([r.vnum, self.world.strip_ansi_codes(r.name), e.direction, e.to_vnum,
                             bool(e.closes), bool(e.locks), known, visited])

        num_visited = len([r for r in rooms if r.last_visited])
        headers = ("_Room", "Name", "Direction", "_To Room", "Closes", "Locks", "Known", "Visited")
        table = tabulate(rows, headers=headers,
                         caption=f"{len(sorted_rooms)} of {len(rooms)} rooms shown.   {num_visited} visited")
        self.output(AbacuraPanel(table, title=f"Rooms in '{area}'"))

    @command()
    def area(self):
        """
        View all known mobs in the current area
        """

        pview = AbacuraPropertyGroup(self.room.area, exclude={"mobs"})
        rows = [(m.name, m.starts_with, m.attack_name, m.level, m.race, m.cls) for m in self.room.area.mobs]
        headers = ["Name", "Starts With", "Attack Name", "Level", "Race", "Class"]
        table = tabulate(rows, headers=headers, title="Known Mobs")
        group = Group(pview, Text(""), table)
        self.output(AbacuraPanel(group, title=f"Area [{self.room.area.name}]"))

    @command(name="mob")
    def mob_command(self, n: int = -1):
        """
        Show mobs in the room and associated atlas information
        """
        if n < 0:
            rows = []
            for i, m in enumerate(self.room.mobs):
                rows.append((i, m.name, m.level, m.quantity, m.description, m.race, m.cls, m.starts_with, m.attack_name))

            tbl = tabulate(rows, headers=("#", "Name", "Level", "Quantity", "Description",
                                          "Race", "Class", "Startswith", "Attack Name"))

            self.output(AbacuraPanel(tbl, title=f"Mobs in [{self.room.vnum}] - {self.room.name}"))
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
