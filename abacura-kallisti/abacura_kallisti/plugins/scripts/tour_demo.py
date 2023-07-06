from abacura.plugins import command, CommandError
from abacura.plugins.events import event
from abacura_kallisti.atlas.room import RoomMessage
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.plugins.scripts.tourguide import TourGuideResponse, TourGuideRequest


class TourDemo(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.last_response: TourGuideResponse | None = None
        self.touring: bool = False
        self.steps_taken: int = 0

    def check_error(self):
        if self.last_response is None:
            self.output(f"> TOUR ERROR - No Response")
            return True

        if self.last_response.error:
            self.output(f"> TOUR ERROR {self.last_response.error}")
            return True

        return False

    @command
    def tour(self, start: bool = False, stop: bool = False):
        """Visit rooms in current area according to area .toml file"""
        if stop:
            self.touring = False
            return

        if start:
            self.start_tour()
            return

        raise CommandError("Please specify --start of --stop")

    @event("lok.room")
    def got_room(self, _message: RoomMessage):
        if not self.touring:
            return

        request = TourGuideRequest()
        self.dispatcher(request)
        self.last_response = request.response

        if self.check_error():
            self.touring = False
            return

        self.advance_tour()

    def start_tour(self):
        request = TourGuideRequest(start_tour=True)
        self.dispatcher(request)
        self.last_response = request.response
        if not self.check_error():
            self.touring = True
            self.steps_taken = 0
            self.advance_tour()

    def advance_tour(self):
        visited = len(self.last_response.visited_rooms)
        reachable = len(self.last_response.reachable_rooms)
        self.debuglog(f"> TOUR: Visited {visited}/{reachable} [{self.steps_taken} steps taken]")

        if self.last_response.completed_tour:
            self.output("TOUR COMPLETE!")
            return

        for cmd in self.last_response.exit.get_commands():
            self.send(cmd)

        self.steps_taken += 1
