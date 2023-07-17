from abacura.plugins import command
from abacura.plugins.scripts import ScriptResult
from abacura.utils.timer import Timer
from abacura_kallisti.atlas.travel_guide import TravelGuide
from abacura_kallisti.atlas.room import Room
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.plugins.scripts.travel import TravelMessage
from abacura.utils.tabulate import tabulate


class TravelHelper(LOKPlugin):
    def __init__(self):
        super().__init__()

    @command
    def path(self, destination: Room, detailed: bool = False):
        """Compute path to a room/location"""
        t = Timer()
        nav = TravelGuide(self.world, self.pc, level=self.msdp.level, avoid_home=False)
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

        rows = []
        for step in nav_path.steps:
            if step.exit.to_vnum in self.world.rooms:
                terrain = self.world.rooms[step.exit.to_vnum].terrain_name
                # area = self.world.rooms[step.exit.to_vnum].area_name

                row = (step.vnum, step.exit.to_vnum, step.exit.get_commands(), step.exit.direction, step.exit.door,
                       bool(step.exit.closes), bool(step.exit.locks), step.cost, terrain)
                rows.append(row)

        tbl = tabulate(rows, headers=("_Vnum", "_To Vnum", "Commands", "Direction", "Door",
                                      "Closes", "Locks", "Cost", "Terrain"),
                       title=f"Path to {destination.vnum}: {speedwalk}", title_justify="left",
                       caption=f"Total Cost [{cost}].  Computed in {1000 * path_elapsed_time:6.3f}ms",
                       caption_justify="right")
        self.output(tbl)

    @command
    def go(self, destination: Room, avoid_home: bool = False):
        """Compute path to a room/location"""
        def go_done(result: ScriptResult):
            self.output(f"[bold purple] #go {result.result}", markup=True)

        tm = TravelMessage(destination=destination, avoid_home=avoid_home, callback_fn=go_done)
        self.dispatch(tm)

        # self.scripts.navigate(go_done, destination, avoid_home)
