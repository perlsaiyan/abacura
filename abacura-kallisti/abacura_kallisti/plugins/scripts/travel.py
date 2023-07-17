from dataclasses import dataclass
from typing import Optional, Callable

from abacura.plugins import action
from abacura.plugins.events import event, AbacuraMessage
from abacura.plugins.scripts import ScriptResult
from abacura_kallisti.atlas.room import RoomMessage, Room
from abacura_kallisti.atlas.travel_guide import TravelGuide, TravelPath
from abacura_kallisti.plugins import LOKPlugin


@dataclass
class TravelMessage(AbacuraMessage):
    destination: Optional[Room] = None
    avoid_home: bool = False
    callback_fn: Optional[Callable] = None
    event_type: str = "lok.script.travel"


class TravelScript(LOKPlugin):
    def __init__(self):
        super().__init__()
        self.navigation_path: Optional[TravelPath] = None
        self.travel_guide: Optional[TravelGuide] = None
        self.retries = 0
        self.callback_fn: Optional[Callable] = None

    @event(trigger="lok.script.travel")
    def handle_travel(self, message: TravelMessage):
        self.callback_fn = message.callback_fn
        self.start_nav(message.destination, message.avoid_home)
        self.retries = 0

    @event(trigger="lok.room")
    def got_room(self, _message: RoomMessage):
        # self.session.output(f"room event {_message.vnum} {_message.room.room_header}")
        if self.navigation_path:
            self.continue_nav()

    # wait 3 seconds and look again
    #    BLOCKING_GUARD = r"^(.*) blocks you from entering the city"

    @action(r"^Your mount is too exhausted.")
    def mount_exhausted(self):
        if self.navigation_path:
            self.cq.add_command(cmd="look", dur=0.1, delay=0, queue_name="Move")

    @action(r"^Alas, you cannot go (.*)")
    def cannot_go(self):
        self.look_and_retry()

    @action(r"^You try to climb but couldn't get a good grip that time.")
    def cannot_climb(self):
        self.look_and_retry()

    @action(r"^(.*) is blocking your way")
    def blocking_way(self):
        self.look_and_retry()

    @action(r"^There's not enough room to fit in there!")
    def no_room(self):
        self.look_and_retry()

    def start_nav(self, destination: Room, avoid_home: bool = False):
        self.output(f"> start_nav {destination.vnum}")
        self.travel_guide = TravelGuide(self.world, self.pc, self.msdp.level, avoid_home)
        nav_path = self.travel_guide.get_path_to_room(self.msdp.room_vnum, destination.vnum, avoid_vnums=set())
        if not nav_path.destination:
            self.end_nav(False, f"Unable to compute path to {destination.vnum}")
            return

        self.dispatch(AbacuraMessage("lok.travel", "start"))
        self.navigation_path = nav_path
        self.cq.add_command(cmd="look", dur=0.1, delay=0, queue_name="Move")

    def end_nav(self, success: bool, message: str):
        self.output(f"> end_nav: {success} {message}")
        self.travel_guide = None
        self.navigation_path = None
        self.dispatch(AbacuraMessage("lok.travel", str(success)))
        self.callback_fn(ScriptResult(success=success, result=message))

    def continue_nav(self):
        if self.msdp.room_vnum == self.navigation_path.destination.vnum:
            self.end_nav(True, "Arrived!")
            return

        room = self.world.rooms.get(self.msdp.room_vnum, None)
        if not room:
            self.end_nav(False, f"unknown room {self.msdp.room_vnum}, navigation halted")
            return

        if not self.navigation_path.truncate_remaining_path(self.msdp.room_vnum):
            self.session.output("LOST PATH")
            self.start_nav(self.navigation_path.destination)
            return

        self.retries = 0

        # TODO: Move logic into navigation path to get next command, handle portals
        for step in self.navigation_path.steps:
            if step.vnum != self.msdp.room_vnum:
                continue

            for cmd in step.exit.get_commands():
                if cmd.startswith("open") and self.msdp.room_exits.get(step.exit.direction) != 'C':
                    continue

                self.cq.add_command(cmd, dur=0, queue_name="Move")

    def look_and_retry(self):
        if self.navigation_path:
            self.retries += 1
            if self.retries > 3:
                self.output(f"Navigation failed after {self.retries} tries")

            wait = 3
            if self.retries == 2:
                self.cq.add_command("breakout", dur=3, queue_name="Priority")
                wait = 6

            self.cq.add_command("look", dur=0.1, delay=wait, queue_name="Move")
