from collections import Counter

from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from abacura.plugins import command
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.atlas.world import Room, Exit
from abacura_kallisti.plugins import LOKPlugin


class WorldHelper(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.wild_grid = WildernessGrid()

    def get_table_of_exits(self, vnum: str):
        exits = []
        for e in self.world.rooms[vnum].exits.values():
            known = e.to_vnum in self.world.rooms
            visited = False
            terrain = ""
            if known:
                to_room = self.world.rooms[e.to_vnum]
                visited = to_room.last_visited not in ['', None]
                terrain = to_room.terrain_name

            exits.append((e.direction, e.to_vnum, e.door, e.commands,
                          bool(e.closes), bool(e.locks), known, visited, terrain, bool(e.deathtrap)))

        exits = sorted(exits)
        caption = ""
        if vnum == self.msdp.room_vnum:
            caption = f"MSDP_EXITS: {str(self.msdp.room_exits)}"

        table = Table(caption=caption, caption_justify="left")
        table.add_column("Direction")
        table.add_column("To", justify="right")
        table.add_column("Door")
        table.add_column("Commands")
        table.add_column("Closes")
        table.add_column("Locks")
        table.add_column("Known")
        table.add_column("Visited")
        table.add_column("Terrain")
        table.add_column("Deathtrap")
        for e in exits:
            table.add_row(*map(str, e))

        return table

    @command()
    def room(self, location: Room = None, delete: bool = False):
        """Display information about a room

        :location A room vnum or location name
        :delete Will delete the room
        """

        if location is None:
            if self.msdp.room_vnum not in self.world.rooms:
                self.output(f"[bright red]Unknown room {self.msdp.room_vnum}", markup=True)
                return

            location = self.world.rooms[self.msdp.room_vnum]
        # if location is None:
        #     if self.msdp.room_vnum in self.world.rooms:
        #         location = self.world.rooms[self.msdp.room_vnum]
        #     else:
        #         self.session.output(f"Unknown room {self.msdp.room_vnum}", actionable=False)
        #         return
        #
        # elif location_vnum not in self.world.rooms:
        #     self.session.output(f"Unknown location {location_vnum}", actionable=False)
        #     return
        # else:
        #     location = self.world.rooms[location_vnum]

        text = Text()

        text.append(f"[{location.vnum}] {location.name}\n\n", style="bold magenta")
        text.append(f"     Area: {location.area_name}\n")

        terrain = location.terrain
        text.append(f"  Terrain: {location.terrain_name} [{terrain.weight}]\n")
        text.append(f"    Flags: {self.get_room_flags(location)}\n")
        text.append(f"  Visited: {location.last_visited}\n")

        if location.area_name == 'The Wilderness':
            x, y = self.wild_grid.get_point(location.vnum)
            ox, oy = self.wild_grid.get_orienteering_point(location.vnum)
            text.append(f"     x, y: {x}, {y} [{ox}, {oy}]\n")
            text.append(f"Harvested: {location.last_harvested}\n")

        location_names = [f"{a.category}.{a.name}" for a in self.locations.get_locations_for_vnum(location.vnum)]
        if len(location_names) > 0:
            text.append(f"Locations: {', '.join(location_names)}\n")

        text.highlight_regex(r"[a-zA-Z]+:", style="bold")

        table = self.get_table_of_exits(location.vnum)
        group = Group(text, table)
        panel = Panel(group)
        self.output(panel, highlight=True)

        if delete:
            self.world.delete_room(location.vnum)
            self.session.output("\n[orange1] ROOM DELETED\n", markup=True)

    @staticmethod
    def get_room_flags(room: Room) -> str:
        flags = ['wild_magic', 'silent', 'set_recall', 'no_recall', 'no_magic', 'narrow',
                 'peaceful', 'deathtrap', 'regen_hp', 'regen_mp', 'regen_sp', 'bank']
        flags = [f.replace('_', ' ') for f in flags if getattr(room, f, False)]
        return ','.join(flags)

    # @command()
    # def roomflags(self, peaceful: bool = False, silent: bool = False,
    #               no_recall: bool = False, no_magic: bool = False, wild_magic: bool = False,
    #               narrow: bool = False):
    #     """Display flags for a room"""
    #     if self.msdp.room_vnum not in self.world.rooms:
    #         raise ValueError('Unknown room [%s]' % self.msdp.room_vnum)
    #
    #     room = self.world.rooms[self.msdp.room_vnum]
    #     # If the parameter is true, toggle the room value.  ^ is an XOR operation for the toggle.
    #     room.peaceful = room.peaceful ^ peaceful
    #     room.silent = room.silent ^ silent
    #     room.no_recall = room.no_recall ^ no_recall
    #     room.no_magic = room.no_magic ^ no_magic
    #     room.wild_magic = room.wild_magic ^ wild_magic
    #     room.narrow = room.narrow ^ narrow
    #
    #     self.session.output("[%s] %s" % (room.vnum, room.name))
    #     room = self.world.rooms[room.vnum]
    #     self.session.output("Flags: %s" % self.get_room_flags(room))

    @command()
    def area(self, area: str = ''):
        """View all known rooms in an area"""
        if area == '':
            if self.msdp.room_vnum in self.world.rooms:
                area = self.world.rooms[self.msdp.room_vnum].area_name
            else:
                raise ValueError('Unknown area')
        else:
            areas = {r.area_name: True for r in self.world.rooms.values()}
            match_areas = [a for a in areas.keys() if a.lower().startswith(area.lower())]
            match_areas.sort(key=lambda a: 100 - abs(len(a) - len(area)))
            if len(match_areas) == 0:
                raise ValueError('Unknown area %s' % area)
            area = match_areas[0]

        rooms = [r for r in self.world.rooms.values() if r.area_name == area]

        sorted_rooms = list(sorted(rooms, key=lambda x: x.vnum))[:300]

        table = Table(caption=f"{len(sorted_rooms)} of {len(rooms)} rooms shown", caption_justify="left")
        table.add_column("Room", justify="right")
        table.add_column("Name")
        table.add_column("Direction")
        table.add_column("To Room")
        table.add_column("Closes")
        table.add_column("Locks")
        table.add_column("Known")
        table.add_column("Visited")

        r: Room
        for r in sorted_rooms:
            e: Exit
            for e in r.exits.values():
                known: bool = e.to_vnum in self.world.rooms
                visited = known and self.world.rooms[e.to_vnum].last_visited

                table.add_row(r.vnum, r.name, e.direction, e.to_vnum, str(bool(e.closes)), str(bool(e.locks)),
                              str(known), str(visited))

        # s = tabulate(table, headers=["Room", "Name", "Exit", "To", "Closes", "Locks", "Known", "Visited"])
        self.session.output(table, actionable=False)

        num_visited = len([r for r in rooms if r.last_visited])
        num_rooms = len(rooms)
        self.session.output(f"\nArea:{area}\n\n  Known Rooms: {num_rooms:5d}\nVisited Rooms: {num_visited:5d}",
                            actionable=False)

    @command()
    def exits(self, direction: str = '', name: str = None, destination: Room = None, delete: bool = False):
        """Add and modify exits"""

        vnum = self.msdp.room_vnum

        if vnum not in self.world.rooms:
            self.session.output(f"[orange1][italic]Unknown room [{vnum}]", highlight=True, markup=True)
            return

        if not direction:
            self.session.output(self.get_table_of_exits(vnum))
            return

        if name:
            to_vnum = None
            if destination is not None and (destination.vnum != self.msdp.room_vnum):
                to_vnum = destination.vnum
            self.world.set_exit(vnum, direction, name, to_vnum)
            self.session.output(f"Set [{vnum}] {direction} name {name}", highlight=True)
            if destination is not None:
                self.session.output(f"Set destination {to_vnum}", highlight=True)
            return

        if delete:
            self.world.del_exit(vnum, direction)
            self.session.output(f"Deleted [{vnum}] {direction}", highlight=True)
            return

        room = self.world.rooms[vnum]
        if direction not in room.exits:
            self.session.output(f"[orange1]Unknown direction {direction} for room [{vnum}]", markup=True)
            return
        e = room.exits[direction]
        properties = [(name, getattr(e, name)) for name in sorted(e.__slots__)]

        tbl = Table(title=f"\n[{vnum}] {direction}", title_justify="left")
        tbl.add_column("Property")
        tbl.add_column("Value", justify="right")
        for p in properties:
            tbl.add_row(*map(str, p))
        self.output(tbl)

    @command
    def sql(self, sql: str, _max_rows: int = 100):
        try:
            cursor = self.world.db_conn.execute(sql)
        except Exception as e:
            self.session.show_exception(str(e), e)
            return

        if not cursor.description:
            self.output("executed")
            return

        title_style = Style(bgcolor="#000040", color="bright_white", bold=True)
        caption_style = Style(bgcolor="#000040", color="white")
        header_style = Style(bgcolor="#000040", color="bright_white")
        border_style = Style(bgcolor="#000040", color="#CCCCCC")
        s1 = Style(bgcolor="#101020", color="white")
        s2 = Style(bgcolor="#202040", color="white")
        tbl = Table(title=f"SQL: {sql}", title_justify="left", title_style=title_style,
                    caption=f" Showing first {_max_rows} rows", caption_justify="left", caption_style=caption_style,
                    row_styles=[s1, s2], header_style=header_style, border_style=border_style)

        rows = list(cursor.fetchmany(_max_rows))

        column_types = []

        for i, column in enumerate(cursor.description):
            c = Counter([type(row[i]) for row in rows])
            column_types.append(c.most_common(1)[0][0])
            justify = "left"
            if column_types[i] in (int, 'int', float, 'float'):
                justify = "right"
            tbl.add_column(column[0], justify=justify)

        for row in rows:
            new_row = []
            for i, v in enumerate(row):
                if column_types[i] in (float, 'float'):
                    new_row.append(format(v, "6.3f"))
                else:
                    new_row.append(str(v))

            tbl.add_row(*new_row)

        self.output(Panel(tbl, style=border_style))
