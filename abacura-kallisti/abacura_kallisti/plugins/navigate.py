from abacura.plugins import command
from abacura.plugins.events import event, AbacuraMessage
from abacura_kallisti.atlas.navigator import Navigator, NavigationPath
from abacura_kallisti.atlas.room import RoomMessage, Room
from abacura_kallisti.plugins import LOKPlugin
from abacura.plugins.events import event
from typing import Optional

from rich.table import Table


class NavigationHelper(LOKPlugin):
    def __init__(self):
        super().__init__()
        self.navigation_path: Optional[NavigationPath] = None
        self.navigator: Optional[Navigator] = None

    @command
    def path(self, destination: Room, detailed: bool = False):
        """Compute path to a room/location"""
        nav = Navigator(self.world, self.pc, level=self.msdp.level, avoid_home=False)
        nav_path = nav.get_path_to_room(self.msdp.room_vnum, destination.vnum, avoid_vnums=set())
        if not nav_path.destination:
            self.output(f"[orange1]Unable to compute path to {destination.vnum}", markup=True)
            return

        cost = nav_path.get_travel_cost()
        speedwalk = nav_path.get_simplified_path()

        if not detailed:
            self.session.output(f"Path to {destination.vnum} is {speedwalk}", highlight=True)
            return

        tbl = Table(caption=f"Path to {destination.vnum} - cost [{cost}]: {speedwalk}", caption_justify="left")
        tbl.add_column("Vnum", justify="right")
        tbl.add_column("To Vnum", justify="right")
        tbl.add_column("Command")
        tbl.add_column("Direction")
        tbl.add_column("Door")
        tbl.add_column("Portal Method")
        tbl.add_column("Closes")
        tbl.add_column("Locks")
        tbl.add_column("Cost")
        tbl.add_column("Terrain")

        for step in nav_path.steps:
            if step.exit.to_vnum in self.world.rooms:
                terrain = self.world.rooms[step.exit.to_vnum].terrain_name
                # area = self.world.rooms[step.exit.to_vnum].area_name

                record = (step.vnum, step.exit.to_vnum, step.get_command(), step.exit.direction, step.exit.door,
                          step.exit.portal_method, bool(step.exit.closes), bool(step.exit.locks), step.cost, terrain)
                tbl.add_row(*map(str, record))

        self.output(tbl)

    @command
    def go(self, destination: Room, avoid_home: bool = False):
        """Compute path to a room/location"""
        self.navigator = Navigator(self.world, self.pc, level=self.msdp.level, avoid_home=avoid_home)
        self.start_nav(destination)

    @event(trigger="lok.room")
    def got_room(self, _message: RoomMessage):
        # self.session.output(f"room event {_message.vnum} {_message.room.room_header}")
        if self.navigation_path:
            self.continue_nav()

    def start_nav(self, destination: Room):
        nav_path = self.navigator.get_path_to_room(self.msdp.room_vnum, destination.vnum, avoid_vnums=set())
        if not nav_path.destination:
            self.output(f"[orange1]Unable to compute path to {destination.vnum}", markup=True)
            return

        self.session.dispatcher(AbacuraMessage(event_type="lok.navigate", value="start"))
        self.navigation_path = nav_path
        self.session.send("look")

    def continue_nav(self):
        if self.msdp.room_vnum == self.navigation_path.destination.vnum:
            self.session.dispatcher(AbacuraMessage(event_type="lok.navigate", value="arrived"))
            self.session.output("[bold purple]Arrived!", markup=True)
            self.navigation_path = None
            return

        room = self.world.rooms.get(self.msdp.room_vnum, None)
        if not room:
            self.session.dispatcher(AbacuraMessage(event_type="lok.navigate", value="failed"))
            self.session.output(f"unknown room {self.msdp.room_vnum}, navigation halted")
            self.navigation_path = None
            return

        for i, step in enumerate(self.navigation_path.steps):
            if self.msdp.room_vnum != step.vnum:
                continue

            if step.open and self.msdp.room_exits.get(step.exit.direction) != 'C':
                continue

            cmd = step.get_command()
            self.session.output(f"[purple]{cmd}", markup=True)
            self.session.send(cmd)

            if step.open:
                continue

            self.navigation_path.steps = self.navigation_path.steps[i:]

            return

        self.session.output("LOST PATH")
        self.start_nav(self.navigation_path.destination)
