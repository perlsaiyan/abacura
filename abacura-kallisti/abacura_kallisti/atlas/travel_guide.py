import heapq
from dataclasses import dataclass
from typing import Dict, Set, List, Generator
from itertools import groupby

from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.atlas.world import World
from abacura_kallisti.atlas.room import Exit, Room, Area
from abacura_kallisti.mud.player import PlayerCharacter
from itertools import chain

HOMETOWN = 'Midgaard City'
HOME_AREA_NAME = 'Mortal Residences'


@dataclass(slots=True)
class TravelStep:
    vnum: str
    exit: Exit
    cost: float


class TravelPath:
    def __init__(self, destination: Room = None):
        self.steps: List[TravelStep] = []
        self.destination: Room = destination

    def add_step(self, step: TravelStep):
        self.steps.append(step)

    def reverse(self):
        self.steps.reverse()

    def truncate_remaining_path(self, current_vnum: str) -> bool:
        """
        Determines if the current_vnum is on the path.
        If it is, it truncates the path to start from that vnum and returns True.
        If it is not on the path, it returns False
        """
        for i, step in enumerate(self.steps):
            if step.vnum == current_vnum:
                self.steps = self.steps[i:]
                return True

        return False

    def get_steps(self, vnum: str) -> Generator[TravelStep, None, None]:
        for step in self.steps:
            if step.vnum == vnum:
                yield step

    def get_travel_cost(self) -> float:
        return sum(s.cost for s in self.steps)

    def get_simplified_path(self):
        #     exits = room.known_exits
        #     exits = [e for e in exits.values() if is_allowed(e.to_vnum)]
        #     exits.sort(key=lambda x: area_tracking[x.to_vnum])
        # return speedwalk style directions
        if len(self.steps) == 0:
            return ''

        commands = [cmd for step in self.steps for cmd in step.exit.get_commands()]
        grouped = [(len(list(g)), cmd) for cmd, g in groupby(commands)]
        simplified = [f"{cnt if cnt > 1 else ''}{cmd}" for cnt, cmd in grouped]

        return ";".join(simplified)


class TravelGuide:

    def __init__(self, world: World, pc: PlayerCharacter, level: int = 0, avoid_home: bool = False):
        super().__init__()
        self.world: World = world
        self.wilderness_grid = WildernessGrid()
        # self.knows_bifrost = self.pc.probably_knows('Bifrost')
        self.exit_costs: dict = {}
        self.pc: PlayerCharacter = pc
        self.level = level
        self.avoid_home = avoid_home

    def get_path_to_room(self, start_vnum: str, goal_vnum: str,
                         avoid_vnums: Set[str], allowed_vnums: Set[str] = None) -> TravelPath:
        try:
            if start_vnum not in self.world.rooms:
                return TravelPath()

            path = next(self._gen_nearest_rooms(start_vnum, {goal_vnum}, avoid_vnums, allowed_vnums))
            return path
        except StopIteration:
            return TravelPath()

    def get_nearest_rooms_in_set(self, start_vnum: str, goal_vnums: Set[str],
                                 avoid_vnums: Set[str] = None, allowed_vnums: Set[str] = None,
                                 max_rooms: int = 1) -> List[TravelPath]:
        if avoid_vnums is None:
            avoid_vnums = set()

        # self.session.debug('NAV avoid %s' % avoid_vnums, show=True)
        found = []
        for path in self._gen_nearest_rooms(start_vnum, goal_vnums, avoid_vnums, allowed_vnums):
            found.append(path)
            if len(found) == max_rooms:
                break

        return found

    # def get_next_command(self, step: TravelStep) -> str:
    #     if not step:
    #         return ""
    #
    #     route_exit: Exit = step.exit
    #     route_direction = route_exit.direction
    #     move_direction = route_direction
    #
    #     room_exits = self.msdp.get_exits()
    #
    #     # self.session.debug("%s %s" % (route_direction, room_exits))
    #     if route_exit.portal_method:
    #         move_direction = route_exit.portal_method + " " + route_direction
    #     elif route_direction in room_exits:
    #         move_direction = route_direction
    #         exit_status = room_exits[route_direction]
    #         # self.session.debug("%s %s " % (route_direction, exit_self.msdp))
    #         if exit_status == "C":
    #             self.session.send("open %s %s" % (route_exit.door or "door", route_direction))
    #         elif exit_status == 'L':
    #             self.session.show_block("Unable to proceed through lock %s" % route_direction)
    #             return ""
    #     elif route_direction not in CARDINAL_DIRECTIONS:
    #         # this is not north, south, east, west, etc., just use the direction as the command
    #         move_direction = route_direction
    #
    #     # self.session.debug(f"Nav direction {move_direction}", show=True)
    #     return move_direction

    def _convert_came_from_to_path(self, dest_vnum: str, came_from: Dict) -> TravelPath:
        if dest_vnum not in self.world.rooms:
            return TravelPath()

        path = TravelPath(self.world.rooms[dest_vnum])

        current_vnum = dest_vnum

        while current_vnum in came_from and came_from[current_vnum][1].to_vnum != '':
            current_vnum, room_exit, cost = came_from[current_vnum]

            path.add_step(TravelStep(current_vnum, room_exit, cost))
            # add command to open door after the door because we will reverse below

        path.reverse()

        # translate from running cost to actual cost per step
        last_cost = 0
        for s in path.steps:
            s.cost, last_cost = s.cost - last_cost, s.cost

        return path

    def _get_exit_cost(self, room_exit: Exit) -> int:
        # special_unlock = room_exit.special_unlock is not None and room_exit.special_unlock != ''
        if room_exit.to_vnum in ['?', 'L'] or room_exit.locks:  # and not special_unlock :
            return -1

        if room_exit.max_level < self.level:
            return -1

        if room_exit.min_level > self.level:
            return -1

        if room_exit.to_vnum not in self.world.rooms:
            return -1

        to_room = self.world.rooms[room_exit.to_vnum]

        if to_room.terrain.impassable:
            return -1

        if to_room.deathtrap:
            return -1

        # prefer not to open doors since it takes another command
        return to_room.terrain.weight + room_exit.weight + room_exit.closes

    def _get_special_exits(self, room_vnum: str) -> Generator:
        current_room = self.world.rooms[room_vnum]

        if current_room.area_name == 'The Wilderness':
            return

        can_go_home = current_room.area_name in [HOMETOWN, HOME_AREA_NAME] and self.pc.home_vnum != '' 
        
        if can_go_home and not self.avoid_home:
            # from_room: str = '3001' if with_group else current_room.vnum
            e = Exit(from_vnum=current_room.vnum, to_vnum=self.pc.home_vnum, direction='home', weight=2)
            yield e

        if current_room.area_name == HOME_AREA_NAME and self.pc.egress_vnum != '' and not self.avoid_home:
            e = Exit(from_vnum=current_room.vnum, to_vnum=self.pc.egress_vnum, direction='depart', weight=2)
            yield e

        can_recall = not current_room.no_recall and not current_room.silent and not current_room.no_magic
        if can_recall and self.pc.recall_vnum != '':
            e = Exit(from_vnum=current_room.vnum, to_vnum=self.pc.recall_vnum, direction='recall', weight=3)
            yield e

    # def _get_area_cost(self, start_vnum: str, room_exit: Exit, goal_vnums: set) -> int:
    #     if len(goal_vnums) != 1:
    #         return 0
    #
    #     start_room = self.world.rooms.get(start_vnum, None)
    #     exit_room = self.world.rooms.get(room_exit.to_vnum, None)
    #     goal_room = self.world.rooms.get(list(goal_vnums)[0], None)
    #
    #     if not start_room or not exit_room or not goal_room:
    #         return 0
    #
    #     egress_room = self.world.rooms.get(self.pc.egress_vnum, None)
    #     egress_area = egress_room.area_name if egress_room else ''
    #
    #     if exit_room.area_name in [HOMETOWN, HOME_AREA_NAME, egress_area]:
    #         return 0
    #
    #     return 0

    def _get_wilderness_cost(self, current_room: Room, room_exit: Exit, goal_vnums: set) -> int:
        cost = 0

        if len(goal_vnums) != 1:
            return cost

        # increase cost if we are going further away from our single goal room
        goal_vnum = list(goal_vnums)[0]
        cur_distance = self.wilderness_grid.get_distance(current_room.vnum, goal_vnum)
        new_distance = self.wilderness_grid.get_distance(room_exit.to_vnum, goal_vnum)
        cost += 5 * (new_distance - cur_distance)

        return cost

    def _gen_nearest_rooms(self, start_vnum: str, goal_vnums: Set[str], avoid_vnums: Set[str],
                           allowed_vnums: Set[str] = None) -> Generator[TravelPath, None, None]:

        # This is a priority queue using heapq, the lowest weight item will heappop() off the list
        frontier = []
        goal_vnums = goal_vnums.copy()
        heapq.heappush(frontier, (0, start_vnum))

        came_from: Dict[str, (str, Exit, int)] = {start_vnum: (start_vnum, Exit(), 0)}
        cost_so_far = {start_vnum: 0}

        n = 0
        while len(frontier) > 0 and n <= 60000:
            n += 1
            current_cost, current_vnum = heapq.heappop(frontier)

            if current_vnum in goal_vnums:
                # self.session.debug('NAV: gen examined %d rooms' % len(came_from))
                yield self._convert_came_from_to_path(current_vnum, came_from)

            current_room = self.world.rooms[current_vnum]
            # exits = self.get_standard_exits(current_room.vnum, self.char_level)

            # if current_room.vnum in self.world.temporary_portals:
            # exits += self.get_temporary_exits(current_room.vnum, self.char_level)

            # if self.check_specials:
            # exits += self.get_special_exits(current_room.vnum)

            for room_exit in chain(current_room.exits.values(),
                                   self._get_special_exits(current_room.vnum)):

                exit_cost = self._get_exit_cost(room_exit)
                if exit_cost < 0:
                    continue

                if current_room.vnum in avoid_vnums:
                    continue

                if room_exit.to_vnum in came_from and room_exit.to_vnum not in goal_vnums:
                    continue

                if allowed_vnums and current_vnum not in allowed_vnums:
                    continue

                # compute weight
                new_cost = cost_so_far.get(current_vnum, 0) + exit_cost

                if current_room.area_name == 'The Wilderness':
                    new_cost += self._get_wilderness_cost(current_room, room_exit, goal_vnums)

                # TODO: Make it optional to try and stay within the area
                # elif len(goal_vnums) == 1:
                #    new_cost += self._get_area_cost(start_vnum, room_exit, goal_vnums)

                # prefer going in the same direction if we are looking for one goal room
                # just because this gives a shorter "speedwalk" view
                # last_exit: Exit = came_from[current_vnum][1]
                # if len(goal_vnums) == 1 and room_exit.direction != last_exit.direction and len(goal_vnums):
                #     new_cost += 0.1

                if room_exit.to_vnum not in cost_so_far or new_cost < cost_so_far[room_exit.to_vnum]:
                    heapq.heappush(frontier, (new_cost, room_exit.to_vnum))
                    # print('Put: ', current_vnum, room_exit.direction, room_exit.to_vnum, new_cost)
                    cost_so_far[room_exit.to_vnum] = new_cost
                    came_from[room_exit.to_vnum] = (current_vnum, room_exit, new_cost)

    def is_navigable_room_in_area(self, area: Area, vnum: str) -> bool:
        vnum_allowed = area.is_allowed_vnum(vnum, self.level)
        vnum_mapped = vnum in self.world.rooms
        if not vnum_allowed or not vnum_mapped:
            return False

        room = self.world.rooms[vnum]
        area_allowed = area.is_allowed_area(room.area_name)
        return vnum_mapped and vnum_allowed and area_allowed

    # def get_avoid_rooms_in_known_area(self, start_vnum: str) -> set:
    #     room: Room = self.world.rooms[start_vnum]
    #     ea = KNOWN_AREAS[room.area_name]
    #     return known_area.get_excluded_room_vnums(self.char_level)
    #
    def get_reachable_rooms_in_known_area(self, start_vnum: str, area: Area,
                                          allowed_rooms: Set[str] = None, max_steps: int = 999999,
                                          consider_locks_reachable: bool = False) -> set:
        visited = set()
        frontier = {start_vnum}
        room: Room = self.world.rooms[start_vnum]

        if area.track_random_portals:
            vnums = [r.vnum for r in self.world.rooms.values() if r.area_name == room.area_name]
            vnums = [v for v in vnums if self.is_navigable_room_in_area(area, v)]
            vnums = [v for v in vnums if allowed_rooms is None or v in allowed_rooms]
            return set(vnums)

        while len(frontier) > 0 and max_steps > 0:
            max_steps -= 1
            room_vnum = frontier.pop()
            if room_vnum not in self.world.rooms:
                continue

            visited.add(room_vnum)
            # room = self.world.rooms[room_vnum]

            for e in self.world.rooms[room_vnum].exits.values():
                if not self.is_navigable_room_in_area(area, e.to_vnum):
                    continue

                if allowed_rooms is not None and e.to_vnum not in allowed_rooms:
                    continue

                unreachable_lock = e.locks and not consider_locks_reachable
                if e.to_vnum not in visited and e.to_vnum not in frontier and not unreachable_lock:
                    frontier.add(e.to_vnum)

        return visited
