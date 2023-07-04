from rich.table import Table

from abacura.plugins import command
from abacura.plugins.scripts import ScriptResult
from abacura.utils.timer import Timer
from abacura_kallisti.atlas.navigator import Navigator
from abacura_kallisti.atlas.room import Room
from abacura_kallisti.plugins import LOKPlugin


class NavigationHelper(LOKPlugin):
    def __init__(self):
        super().__init__()

    @command
    def path(self, destination: Room, detailed: bool = False):
        """Compute path to a room/location"""
        t = Timer()
        nav = Navigator(self.world, self.pc, level=self.msdp.level, avoid_home=False)
        t.start()
        nav_path = nav.get_path_to_room(self.msdp.room_vnum, destination.vnum, avoid_vnums=set())
        path_elapsed_time = t.stop()
        if not nav_path.destination:
            self.output(f"[orange1]Unable to compute path to {destination.vnum}", markup=True)
            return

        cost = nav_path.get_travel_cost()
        speedwalk = nav_path.get_simplified_path()

        if not detailed:
            self.session.output(f"Path to {destination.vnum} is {speedwalk}", highlight=True)
            return

        tbl = Table(title=f"Path to {destination.vnum}: {speedwalk}", title_justify="left",
                    caption=f"Total Cost [{cost}].  Computed in {1000*path_elapsed_time:6.3f}ms", caption_justify="right")

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
        self.scripts.navigate(self.go_done, destination, avoid_home)

    def go_done(self, result: ScriptResult):
        self.output(f"[bold purple] @Go Result {result.success} {result.result}", markup=True)
