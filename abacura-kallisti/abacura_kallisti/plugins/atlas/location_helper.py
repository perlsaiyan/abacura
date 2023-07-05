from rich.table import Table

from abacura.plugins import command
from abacura_kallisti.atlas.world import Room
from abacura_kallisti.plugins import LOKPlugin


class LocationHelper(LOKPlugin):

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
