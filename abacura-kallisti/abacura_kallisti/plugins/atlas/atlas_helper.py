from abacura.plugins import command
from abacura_kallisti.atlas.terrain import get_terrain
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.atlas.world import Room, Exit
from abacura_kallisti.atlas.navigator import Navigator
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Group


class WorldPlugin(LOKPlugin):

    def get_table_of_exits(self, vnum: str):
        exits = []
        for e in self.world.get_exits(vnum).values():
            known = e.to_vnum in self.world.rooms
            visited = False
            terrain = ""
            if known:
                visited = self.world.get_tracking(e.to_vnum).last_visited is not None
                terrain = self.world.rooms[e.to_vnum].terrain

            exits.append((e.direction, e.to_vnum, e.door, e.portal, e.portal_method,
                          bool(e.closes), bool(e.locks), known, visited, terrain, bool(e.deathtrap)))

        exits = sorted(exits)
        caption = ""
        if vnum == self.msdp.room_vnum:
            caption = f"MSDP_EXITS: {str(self.msdp.room_exits)}"

        table = Table(caption=caption, caption_justify="left")
        table.add_column("Direction")
        table.add_column("To", justify="right")
        table.add_column("Door")
        table.add_column("Portal")
        table.add_column("Portal Method")
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

        tr = self.world.get_tracking(location.vnum)
        text.append(f"[{location.vnum}] {location.name}\n\n", style="bold magenta")
        text.append(f"     Area: {location.area_name}\n")

        terrain = get_terrain(location.terrain)
        terrain_weight = terrain.weight if terrain else -1
        text.append(f"  Terrain: {location.terrain} [{terrain_weight}]\n")
        text.append(f"    Flags: {self.get_room_flags(location)}\n")
        text.append(f"  Visited: {tr.last_visited}\n")

        if location.area_name == 'The Wilderness':
            x, y = self.wild_grid.get_point(location.vnum)
            ox, oy = self.wild_grid.get_orienteering_point(location.vnum)
            text.append(f"     x, y: {x}, {y} [{ox}, {oy}]\n")
            text.append(f"Harvested: {tr.last_harvested}\n")

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
                visited = known and self.world.get_tracking(e.to_vnum).last_visited is not None

                table.add_row(r.vnum, r.name, e.direction, e.to_vnum, str(bool(e.closes)), str(bool(e.locks)),
                              str(known), str(visited))

        # s = tabulate(table, headers=["Room", "Name", "Exit", "To", "Closes", "Locks", "Known", "Visited"])
        self.session.output(table, actionable=False)

        num_visited = len([r for r in rooms if self.world.get_tracking(r.vnum).last_visited is not None])
        num_rooms = len(rooms)
        self.session.output(f"\nArea:{area}\n\n  Known Rooms: {num_rooms:5d}\nVisited Rooms: {num_visited:5d}",
                            actionable=False)

    @command(name="locations")
    def location_cmd(self, location: str = None, destination: Room = None, delete: bool = False, add: bool = False):
        """View and modify room locations"""

        if location is None:
            tbl = Table(title="Location Categories")
            tbl.add_column("Category Name")

            for c in self.locations.get_categories():
                tbl.add_row(c)

            self.session.output(tbl)
            return

        s = location.split(".")
        if len(s) > 2:
            raise ValueError('Location should be of the format <category>.<name>')

        if add and delete:
            raise ValueError('Cannot specify both add and delete')

        category = s[0]

        if len(s) == 1:
            if add or delete:
                raise ValueError('Cannot add or delete category directly, use <category>.<name>')

            if category not in self.locations.get_categories():
                raise ValueError(f'Unknown category {category}')

            rooms = []

            # nav = Navigator(check_specials=True)

            for a in self.locations.get_category(category):
                room_name = self.world.rooms[a.vnum].name if a.vnum in self.world.rooms else "<missing>"
                area_name = self.world.rooms[a.vnum].area_name if a.vnum in self.world.rooms else "<missing>"

                # don't try to compute navigation between wilderness and non-wilderness areas
                # cost = 0
                # if not ('The Wilderness' in [self.msdp.area_name, area_name] and self.msdp.area_name != area_name):
                #     path = nav.get_path_to_room(self.msdp.room_vnum, a.vnum, set())
                #     cost = round(path.get_travel_cost())

                rooms.append((a.name, a.vnum, room_name[:30], area_name[:30]))

            tbl: Table = Table(title=f"{category}: locations")
            tbl.add_column("Name")
            tbl.add_column("VNUM")
            tbl.add_column("Room Name")
            tbl.add_column("Area")

            for r in rooms:
                tbl.add_row(*r)
            self.session.output(tbl)                
            return

        existing_location = self.locations.get_location(location)

        if delete:
            if existing_location is None:
                raise ValueError(f"Unknown location {location}")

            self.locations.delete_location(location)
            self.session.output("Alias %s deleted" % location)

            return

        if add:
            if existing_location is not None:
                raise ValueError(f"Alias %s already exists {location}")

            if destination is None:
                destination = self.world.rooms[self.msdp.room_vnum]

            self.locations.add_location(location, destination.vnum)
            self.session.output("Alias %s added for [%s]" % (location, destination.vnum))
            return

        if existing_location is None:
            raise ValueError(f"Unknown location '{location}'")

        if existing_location.vnum not in self.world.rooms:
            raise ValueError(f'Alias {location} points to missing room {existing_location.vnum}')

        location_room = self.world.rooms[existing_location.vnum]
        self.session.output(f"{location} points to {existing_location.vnum} in {location_room.area_name}")

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
