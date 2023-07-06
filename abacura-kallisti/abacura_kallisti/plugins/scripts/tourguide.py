import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from abacura_kallisti.atlas.navigator import Navigator, NavigationPath
from abacura_kallisti.atlas.room import Area, Exit
from abacura_kallisti.plugins import LOKPlugin
from abacura.plugins.events import event, AbacuraMessage


@dataclass
class TourGuideResponse:
    completed_tour: bool = False
    exit: Optional[Exit] = None
    error: str = ''
    visited_rooms: set = field(default_factory=set)
    unvisited_rooms: set = field(default_factory=set)
    reachable_rooms: set = field(default_factory=set)


@dataclass
class TourGuideRequest(AbacuraMessage):
    """Message to start a tour"""
    event_type: str = "lok.tourguide"
    start_tour: bool = False
    follow_blood: bool = False
    response: Optional[TourGuideResponse] = None


class TourGuide(LOKPlugin):
    """Visit rooms in an area using parameters specified in <area>.toml file"""

    def __init__(self):
        super().__init__()
        self.area: Area = self.room.area
        self.navigator = Navigator(self.world, self.pc, self.msdp.level, True)
        self.reachable_rooms: set = set()
        self.visited_rooms: set = set()
        self.unvisited_rooms: set = set()
        self.telluria_region = 'start'
        self.telluria_moves = []

    def is_allowed_room(self, vnum: str):
        if vnum not in self.world.rooms:
            return False

        return self.area.is_allowed_vnum(vnum, self.msdp.level)

    @event("lok.tourguide")
    def handle_request(self, message: TourGuideRequest):
        if message.start_tour:
            self.start_tour()

        if self.msdp.room_vnum in self.unvisited_rooms:
            self.unvisited_rooms.remove(self.msdp.room_vnum)

        message.response = self.get_next_step(message.follow_blood)
        self.visited_rooms.add(self.msdp.room_vnum)
        message.response.visited_rooms = self.visited_rooms
        message.response.unvisited_rooms = self.unvisited_rooms
        message.response.reachable_rooms = self.reachable_rooms

    def start_tour(self):
        # if self.area.name == '':
        #     return TourGuideResponse(error="Tour: Unknown area")

        self.visited_rooms = set()
        self.area = self.room.area
        self.telluria_region = 'start'
        self.telluria_moves = ''

        self.reachable_rooms = self.navigator.get_reachable_rooms_in_known_area(self.msdp.room_vnum, self.area)

        if len(self.area.rooms_to_scout):
            self.unvisited_rooms = {vnum for vnum in self.unvisited_rooms if vnum in self.area.rooms_to_scout}
            # self.metrics.info['rooms_to_scout'] = len(self.area.rooms_to_scout)
        else:
            self.unvisited_rooms = self.reachable_rooms.copy()

    def get_next_step(self, follow_blood: bool = False) -> TourGuideResponse:
        if self.area.name == '':
            return TourGuideResponse(error="Unknown area")
        if self.area.route not in ['LRV', 'TD', 'NUP', 'NU']:
            return TourGuideResponse(error=f"Unknown route method {self.area.route}")

        if self.area.route == 'TD':
            return self.next_step_telluria()

        if follow_blood and self.room.blood_trail:
            trail_step = self.follow_trail(self.room.blood_trail)
            if trail_step.exit:
                return trail_step

        if len(self.unvisited_rooms) == 0:
            return TourGuideResponse(completed_tour=True)

        if self.area.route == 'NU':
            return self.next_step_nu()
        elif self.area.route == 'NUP':
            return self.next_step_nu_pocket()

        return self.next_step_lrv()

    def follow_trail(self, blood_trail: str) -> TourGuideResponse:
        for e in self.msdp.room_exits.items():
            # don't keep revisiting the same blood trail, make sure it's been 3 seconds since we last went there
            last_visited_seconds = (datetime.utcnow() - self.get_last_visited(e[1])).total_seconds()
            if e[0] in [blood_trail] and last_visited_seconds >= 3 and self.is_allowed_room(e[1]):
                # self.metrics.misc['scout_trail'] += 1
                return TourGuideResponse(exit=Exit(direction=e[0], to_vnum=e[1]))

        return TourGuideResponse(exit=None)

    def next_step_nu(self) -> TourGuideResponse:
        """Choose exit to head towards the nearest unvisited room"""
        avoid = self.area.get_excluded_room_vnums(self.msdp.level)
        found = self.navigator.get_nearest_rooms_in_set(self.msdp.room_vnum,
                                                        self.unvisited_rooms, avoid, self.reachable_rooms)
        if len(found) == 0:
            return TourGuideResponse(error=f"NU: No rooms found {self.msdp.room_vnum}")

        path: NavigationPath = found[0]
        # self.session.debug('NU: %s -> %s' % (self.msdp.room_vnum, dest.vnum))

        if path is None or len(path.steps) == 0:
            return TourGuideResponse(error=f'NU: [{self.msdp.room_vnum}] - no path to [{found[0].destination.vnum}]')

        # self.session.debug('NU: [%d] steps %s -> %s [%s]' % (len(path.steps), e.from_vnum, e.to_vnum, e.direction))

        return TourGuideResponse(exit=path.steps[0].exit)

    def next_step_nu_pocket(self) -> TourGuideResponse:
        cost_range = 80
        scan_rooms = 8
        max_pocket_size = 50

        avoid = self.area.get_excluded_room_vnums(self.msdp.level)

        # print("avoid", avoid)
        near = []
        best_cost = 9999

        for path in self.navigator.get_nearest_rooms_in_set(self.msdp.room_vnum, self.unvisited_rooms,
                                                            avoid, self.reachable_rooms, max_rooms=scan_rooms):
            if len(path.steps) == 0:
                continue

            cost = path.get_travel_cost()
            if cost > best_cost + cost_range:
                break

            # print("%5s: %4d/%4d [%3d steps]" % (cur_vnum, cost, best_cost, len(path.steps)))
            best_cost = min(cost, best_cost)

            pocket = self.navigator.get_reachable_rooms_in_known_area(path.destination.vnum, self.area,
                                                                      self.unvisited_rooms, max_pocket_size)
            pocket_size = len(pocket)
            near.append((path, cost, pocket_size))

        if len(near) == 0:
            return TourGuideResponse(error=f"NUP: No room found [{self.msdp.room_vnum}]")

        # sort by pocket_size, then cost
        near.sort(key=lambda x: (x[2], x[1]))
        best_path = near[0][0]

        return TourGuideResponse(exit=best_path.steps[0].exit)

    def next_step_lrv(self) -> TourGuideResponse:
        """Choose an exit based on least recently visited vnum"""
        exits = self.room.exits.values()
        allowed = [e for e in exits if self.area.is_allowed_vnum(e.to_vnum) and e.to_vnum in self.world.rooms]
        if len(allowed) == 0:
            return TourGuideResponse(error=f"LRV: No exit found [{self.room.vnum}]")

        ordered = sorted(allowed, key=lambda x: (self.world.rooms[x.to_vnum], random.random))
        return TourGuideResponse(exit=ordered[0])

    def next_step_telluria(self) -> TourGuideResponse:
        # throw in a couple extra moves to get back to center just in case
        routes = {'east': 'eeeeenwwwwwneeeeenwwwwwneeeeesssswwwww' + 'ssww',
                  'west': 'wwwwwseeeeeswwwwwseeeeeswwwwwnnnneeeee' + 'nnee',
                  'north': 'wwwwwneeeeenwwwwwneeeeenwwwwwsssseeeee' + 'ssee'}

        if self.msdp.room_vnum == '34595':
            # self.metrics.info['outpost_visited'] = self.metrics.info.get('outpost_visited', 0) + 1
            if self.telluria_region == 'west':
                self.telluria_region = 'start'
                self.telluria_moves = ''

                return TourGuideResponse(completed_tour=True)

            regions = {'start': 'east', 'east': 'north', 'north': 'west'}

            self.telluria_region = regions[self.telluria_region]
            self.telluria_moves = routes[self.telluria_region]

            return TourGuideResponse(exit=Exit(direction=self.telluria_region))

        while len(self.telluria_moves) > 0:
            move = self.telluria_moves[0]
            self.telluria_moves = self.telluria_moves[1:]
            for k in self.msdp.room_exits.keys():
                if k.startswith(move):
                    return TourGuideResponse(exit=Exit(direction=move))

        return TourGuideResponse(error=f"Telluria: out of moves")
