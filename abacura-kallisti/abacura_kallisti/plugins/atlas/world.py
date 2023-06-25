from abacura.plugins import command
from abacura_kallisti.atlas.terrain import TERRAIN
from abacura_kallisti.mud.player import PlayerCharacter
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.atlas.world import Room, Exit
from abacura_kallisti.atlas.navigator import Navigator


class WorldPlugin(LOKPlugin):

    @command()
    def room(self, location_vnum: str = None, delete: bool = False):
        """Display information about a room"""
        
        if location_vnum is None:
            location = self.world.rooms[self.msdp.room_vnum]
        elif location_vnum not in self.world.rooms:
            self.session.output(f"Unknown location {location_vnum}", actionable=False)
            return
        else:
            location = self.world.rooms[location_vnum]

        tr = self.world.get_tracking(location.vnum)
        self.session.output("[%s] %s" % (location.vnum, location.name))
        self.session.output("Area: %s" % location.area_name)
        terrain = TERRAIN.get(location.terrain, None)
        terrain_weight = terrain.weight if terrain else -1
        self.session.output("Terrain: %s [%d]" % (location.terrain, terrain_weight))
        self.session.output("Flags: %s" % self.get_room_flags(location))
        self.session.output("Visited: %s, %s" % (tr.last_visited is not None, tr.last_visited))

        if location.area_name == 'The Wilderness':
            x, y = self.wild_grid.get_point(location.vnum)
            ox, oy = self.wild_grid.get_orienteering_point(location.vnum)
            self.session.output("x, y: %d,%d [%d, %d]" % (x, y, ox, oy))
            self.session.output("Harvested: %s" % tr.last_harvested)

        # alias_names = [f"{a.category}.{a.name}" for a in self.world.get_aliases_for_vnum(location.vnum)]
        # if len(alias_names) > 0:
        #     self.session.output("Aliases: " + ", ".join(alias_names))
        # self.session.output("")

        if delete:
            self.world.delete_room(location.vnum)
            self.session.output("deleted")
            return

        exits = []
        for e in self.world.get_exits(location.vnum).values():
            known = e.to_vnum in self.world.rooms
            visited = False
            terrain = ""
            if known:
                visited = self.world.get_tracking(e.to_vnum).last_visited is not None
                terrain = self.world.rooms[e.to_vnum].terrain

            exits.append([e.direction, e.to_vnum, e.door, e.portal, e.portal_method,
                          e.closes, e.locks, known, visited, terrain, e.deathtrap])

        exits = sorted(exits)
        # s = tabulate(exits, headers=["Exit", "To", "Door", "Portal", "Method",
        #                              "Closes", "Locks", "Known", "Visited", "Terrain", "Deathtrap"])

        self.session.output(exits)

        if location.vnum == self.msdp.room_vnum:
            self.session.output("\nMSDP_EXITS: " + str(self.msdp.room_exits))

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

        table = []
        r: Room
        for r in sorted(rooms, key=lambda x: x.vnum):
            e: Exit
            for e in r.exits.values():
                known: bool = e.to_vnum in self.world.rooms
                visited = known and self.world.get_tracking(e.to_vnum).last_visited is not None

                record = (r.vnum, r.name, e.direction, e.to_vnum, e.closes, e.locks, known, visited)
                table.append(record)

        table = table[:500]
        # s = tabulate(table, headers=["Room", "Name", "Exit", "To", "Closes", "Locks", "Known", "Visited"])
        self.session.output(table, actionable=False)

        num_visited = len([r for r in rooms if self.world.get_tracking(r.vnum).last_visited is not None])
        num_rooms = len(rooms)
        self.session.output(f"\nArea:{area}\n\n  Known Rooms: {num_rooms:5d}\nVisited Rooms: {num_visited:5d}",
                            actionable=False)

    @command
    def path(self, vnum: str = '3001', detailed: bool = False):
        nav = Navigator(self.world, self.session.pc, False)
        nav_path = nav.get_path_to_room(self.msdp.room_vnum, vnum, avoid_vnums=set())
        self.session.output(f"Path to {vnum} is {nav_path.get_simplified_path()}")
        if detailed:
            for step in nav_path.steps:
                if step.exit.to_vnum in self.world.rooms:
                    terrain = self.world.rooms[step.exit.to_vnum].terrain
                    # area = self.world.rooms[step.exit.to_vnum].area_name

                    record = (step.vnum, step.exit.direction, step.exit.to_vnum, step.exit.door,
                              step.exit.portal_method, step.exit.closes, step.exit.locks, step.cost, terrain)

                    self.output(record)
