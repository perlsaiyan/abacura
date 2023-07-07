from typing import Optional

from abacura.plugins import command, CommandError
from abacura.plugins.events import event
from abacura_kallisti.atlas.room import RoomMessage
from abacura_kallisti.atlas.tour_guide import TourGuide
from abacura_kallisti.plugins import LOKPlugin

from rich.table import Table


class TourDemo2(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.tour_guide: Optional[TourGuide] = None
        self.steps_taken: int = 0

    @command
    def tour2(self, start: bool = False, stop: bool = False, _route: str = '', reach: bool = False):
        """Visit rooms in current area according to area .toml file

        :start Start a tour
        :stop Stop the tour
        :_route Use alternate route method: LRV, NU, or NUP
        """

        if stop:
            self.tour_guide = None
            return

        if start:
            self.tour_guide = TourGuide(self.room.area, self.world, self.pc, self.msdp.level, _route)
            self.steps_taken = 0
            self.advance_tour()
            return

        if reach:
            self.show_reach(_route)
            return

        raise CommandError("Please specify --start or --stop")

    def show_reach(self, route: str = ''):
        tg = TourGuide(self.room.area, self.world, self.pc, self.msdp.level, route)
        response = tg.get_next_step(self.room)
        if response.error:
            self.output(f"[orange1]{response.error}", markup=True)
            return

        rooms = sorted(list(response.reachable_rooms))
        tbl = Table(title=f"Reachable rooms in {self.room.area_name} using {response.route}",
                    caption=f"{len(rooms)} rooms reachable",
                    title_justify="left", caption_justify="left")

        tbl.add_column("Vnum")
        tbl.add_column("Name")
        tbl.add_column("Terrain")
        tbl.add_column("Area")

        for room_vnum in rooms:
            room = self.world.rooms[room_vnum]
            tbl.add_row(room.vnum, room.name, room.terrain_name, room.area_name)

        self.output(tbl)

    @event("lok.room")
    def got_room(self, _message: RoomMessage):
        if not self.tour_guide:
            return

        self.advance_tour()

    def advance_tour(self):
        response = self.tour_guide.get_next_step(self.room)


        if response.error:
            self.output(f"> TOUR ERROR {response.error}")
            self.tour_guide = None
            return True

        visited = len(response.visited_rooms)
        reachable = len(response.reachable_rooms)
        self.debuglog(f"> TOUR: Visited {visited}/{reachable} [{self.steps_taken} steps taken]")

        if response.completed_tour:
            self.output("TOUR COMPLETE!")
            self.tour_guide = None
            return

        for cmd in response.exit.get_commands():
            self.send(cmd)

        self.steps_taken += 1
