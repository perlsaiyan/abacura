from abacura.plugins import command, CommandError
from abacura_kallisti.atlas.world import Room
from abacura_kallisti.plugins import LOKPlugin
from abacura.utils.renderables import tabulate, AbacuraPanel


class LocationHelper(LOKPlugin):

    @command(name="locations")
    def location_cmd(self, location: str = None, destination: Room = None, delete: bool = False, add: bool = False):
        """
        View and modify room locations

        Submit without arguments to view a list of locations

        :param location: Use <category.name> format.  Use just category to view a list.
        :param destination: A room vnum of the location, defaults to current room
        :param delete: Delete a location
        :param add: Add a location
        """

        if location is None:
            rows = [(k, v) for k, v in self.locations.get_categories().items()]
            tbl = tabulate(rows, headers=("Category", "# Locations"))
            self.output(AbacuraPanel(tbl, title="Locations"))
            return

        s = location.split(".")
        if len(s) > 2:
            raise CommandError('Location should be of the format <category>.<name>')

        if add and delete:
            raise CommandError('Cannot specify both add and delete')

        category = s[0]

        if len(s) == 1:
            if add or delete:
                raise CommandError('Cannot add or delete category directly, use <category>.<name>')

            if category not in self.locations.get_categories():
                raise CommandError(f'Unknown category {category}')

            rooms = []

            # nav = TravelGuide(check_specials=True)

            for a in self.locations.get_category(category):
                room_name = self.world.rooms[a.vnum].name if a.vnum in self.world.rooms else "<missing>"
                area_name = self.world.rooms[a.vnum].area_name if a.vnum in self.world.rooms else "<missing>"

                # don't try to compute navigation between wilderness and non-wilderness areas
                # cost = 0
                # if not ('The Wilderness' in [self.msdp.area_name, area_name] and self.msdp.area_name != area_name):
                #     path = nav.get_path_to_room(self.msdp.room_vnum, a.vnum, set())
                #     cost = round(path.get_travel_cost())

                rooms.append((a.name, a.vnum, room_name[:30], area_name[:30]))

            tbl = tabulate(rooms, headers=("Name", "Vnum", "Room Name", "Area"))
            self.output(AbacuraPanel(tbl, title=f"{category}: locations"))
            return

        existing_location = self.locations.get_location(location)

        if delete:
            if existing_location is None:
                raise CommandError(f"Unknown location {location}")

            self.locations.delete_location(location)
            self.session.output("Alias %s deleted" % location)

            return

        if add:
            if existing_location is not None:
                raise CommandError(f"Alias %s already exists {location}")

            if destination is None:
                destination = self.world.rooms[self.msdp.room_vnum]

            self.locations.add_location(location, destination.vnum)
            self.session.output("Alias %s added for [%s]" % (location, destination.vnum))
            return

        if existing_location is None:
            raise CommandError(f"Unknown location '{location}'")

        if existing_location.vnum not in self.world.rooms:
            raise CommandError(f'Alias {location} points to missing room {existing_location.vnum}')

        location_room = self.world.rooms[existing_location.vnum]
        self.session.output(f"{location} points to {existing_location.vnum} in {location_room.area_name}")
