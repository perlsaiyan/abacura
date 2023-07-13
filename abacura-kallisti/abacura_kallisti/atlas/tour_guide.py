import random
from dataclasses import dataclass, field
from typing import Optional

from abacura_kallisti.atlas.navigator import Navigator, NavigationPath
from abacura_kallisti.atlas.room import Area, Exit, ScannedRoom
from abacura_kallisti.atlas.world import World
from abacura_kallisti.mud.player import PlayerCharacter


@dataclass
class TourGuideResponse:
    completed_tour: bool = False
    exit: Optional[Exit] = None
    error: str = ''
    route: str = ''
    visited_rooms: set = field(default_factory=set)
    unvisited_rooms: set = field(default_factory=set)
    reachable_rooms: set = field(default_factory=set)


class TourGuide:
    """Visit rooms in an area using parameters specified in <area>.toml file"""

    # dependencies
    # self.msdp.level, self.msdp.room_vnum
    # self.room.area (what area are we running), self.room.exits (can be inferred from msdp.room_vnum)
    # self.room.blood_trail (needed to follow tracks, but not needed for a tour)
    # For navigator:
    #    self.world
    #    self.pc
    #
    # Init Dependencies:
    #   World, pc, area , level
    #
    # Advance  / Next Dependencies:
    #   room_vnum, msdp.room_exits

    def __init__(self, area: Area, world: World, pc: PlayerCharacter, level: int, override_route: str = ''):
        super().__init__()
        self.area: Area = area
        self.world: World = world
        self.level = level
        self.navigator = Navigator(world, pc, level, avoid_home=True)

        self.route_method = override_route if override_route != '' else self.area.route

        self.reachable_rooms: set = set()
        self.visited_rooms: set = set()
        self.unvisited_rooms: set = set()

        self.telluria_region = 'start'
        self.telluria_moves = []

        self.started: bool = False

    def _start(self, scanned_room: ScannedRoom):
        self.visited_rooms: set = set()
        self.reachable_rooms: set = self.navigator.get_reachable_rooms_in_known_area(scanned_room.vnum, self.area)
        if len(self.area.rooms_to_scout):
            self.unvisited_rooms = {vnum for vnum in self.unvisited_rooms if vnum in self.area.rooms_to_scout}
            # self.metrics.info['rooms_to_scout'] = len(self.area.rooms_to_scout)
        else:
            self.unvisited_rooms = self.reachable_rooms.copy()

        self.started = True

    def get_next_step(self, scanned_room: ScannedRoom) -> TourGuideResponse:

        if not self.started:
            self._start(scanned_room)

        if self.area.name == '':
            return TourGuideResponse(error="Unknown area")

        if self.route_method not in ['LRV', 'TD', 'NUP', 'NU']:
            return TourGuideResponse(error=f"Unknown route method {self.route_method}")

        if scanned_room.vnum not in self.world.rooms and self.route_method != "TD":
            return TourGuideResponse(error="Unknown room")

        if len(self.unvisited_rooms) == 0:
            return TourGuideResponse(completed_tour=True)

        if scanned_room.vnum in self.reachable_rooms:
            self.visited_rooms.add(scanned_room.vnum)

        if scanned_room.vnum in self.unvisited_rooms and self.route_method != "TD":
            self.unvisited_rooms.remove(scanned_room.vnum)

        if len(self.unvisited_rooms) == 0:
            return TourGuideResponse(completed_tour=True, route=self.route_method, visited_rooms=self.visited_rooms,
                                     unvisited_rooms=self.unvisited_rooms, reachable_rooms=self.reachable_rooms)

        if self.route_method == 'TD':
            response = self._next_step_telluria(scanned_room)
        elif self.route_method == 'NU':
            response = self._next_step_nu(scanned_room)
        elif self.route_method == 'NUP':
            response = self._next_step_nu_pocket(scanned_room)
        else:
            response = self._next_step_lrv(scanned_room)

        response.route = self.route_method
        response.visited_rooms = self.visited_rooms
        response.unvisited_rooms = self.unvisited_rooms
        response.reachable_rooms = self.reachable_rooms
        return response

    def _next_step_nu(self, scanned_room: ScannedRoom) -> TourGuideResponse:
        """Choose exit to head towards the nearest unvisited room"""
        avoid = self.area.get_excluded_room_vnums(self.level)
        found = self.navigator.get_nearest_rooms_in_set(scanned_room.vnum,
                                                        self.unvisited_rooms, avoid, self.reachable_rooms)
        if len(found) == 0:
            return TourGuideResponse(error=f"NU: No rooms found {scanned_room.vnum}")

        path: NavigationPath = found[0]
        # self.session.debug('NU: %s -> %s' % (self.msdp.room_vnum, dest.vnum))

        if path is None or len(path.steps) == 0:
            return TourGuideResponse(error=f'NU: [{scanned_room.vnum}] - no path to [{found[0].destination.vnum}]')

        # self.session.debug('NU: [%d] steps %s -> %s [%s]' % (len(path.steps), e.from_vnum, e.to_vnum, e.direction))

        return TourGuideResponse(exit=path.steps[0].exit)

    def _next_step_nu_pocket(self, scanned_room: ScannedRoom) -> TourGuideResponse:
        cost_range = 80
        scan_rooms = 8
        max_pocket_size = 50

        avoid = self.area.get_excluded_room_vnums(self.level)

        # print("avoid", avoid)
        near = []
        best_cost = 9999

        for path in self.navigator.get_nearest_rooms_in_set(scanned_room.vnum, self.unvisited_rooms,
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
            return TourGuideResponse(error=f"NUP: No room found [{scanned_room.vnum}]")

        # sort by pocket_size, then cost
        near.sort(key=lambda x: (x[2], x[1]))
        best_path = near[0][0]

        return TourGuideResponse(exit=best_path.steps[0].exit)

    def _next_step_lrv(self, scanned_room: ScannedRoom) -> TourGuideResponse:
        """Choose an exit based on least recently visited vnum"""
        exits = scanned_room.exits.values()

        def _is_allowed_room(vnum: str):
            if vnum not in self.world.rooms:
                return False

            return self.area.is_allowed_vnum(vnum, self.level)

        allowed = [e for e in exits if _is_allowed_room(e.to_vnum)]
        if len(allowed) == 0:
            return TourGuideResponse(error=f"LRV: No exit found [{scanned_room.vnum}]")

        ordered = sorted(allowed, key=lambda x: (self.world.rooms[x.to_vnum].last_visited, random.random))
        return TourGuideResponse(exit=ordered[0])

    def _next_step_telluria(self, scanned_room: ScannedRoom) -> TourGuideResponse:
        # throw in a couple extra moves to get back to center just in case
        routes = {'east': 'eeeeenwwwwwneeeeenwwwwwneeeeesssswwwww' + 'ssww',
                  'west': 'wwwwwseeeeeswwwwwseeeeeswwwwwnnnneeeee' + 'nnee',
                  'north': 'wwwwwneeeeenwwwwwneeeeenwwwwwsssseeeee' + 'ssee'}

        if scanned_room.vnum == '34595':
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
            for k in scanned_room.msdp_exits.keys():
                if k.startswith(move):
                    return TourGuideResponse(exit=Exit(direction=move))

        return TourGuideResponse(error=f"Telluria: out of moves")
