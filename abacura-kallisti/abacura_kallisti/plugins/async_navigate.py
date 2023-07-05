import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

from textual.worker import Worker, WorkerState

from abacura.plugins import command
from abacura.plugins.events import event, AbacuraMessage
from abacura_kallisti.atlas.navigator import Navigator
from abacura_kallisti.atlas.room import RoomMessage, Room
from abacura_kallisti.plugins import LOKPlugin


class AsyncNavigation(LOKPlugin):
    def __init__(self):
        super().__init__()
        self.q = asyncio.Queue()
        self.worker: Optional[Worker] = None
        self.destination: Optional[Room] = None

        self.add_ticker(0.1, self.check_worker, repeats=-1, name="check_worker")

    def check_worker(self):
        # self.output("check_worker")
        if not self.worker:
            return

        if self.worker.state == WorkerState.ERROR:
            error = getattr(self.worker, "_error")
            if error:
                self.session.show_exception(error, error)

            self.remove_ticker("check_worker")

        if self.worker.state in (WorkerState.SUCCESS, WorkerState.CANCELLED):
            self.output(f"Async Nav DONE {self.worker.name}: {self.worker.state} - {self.worker.result}")
            self.remove_ticker("check_worker")

    async def wait_for_condition(self, condition, seconds=30):
        self.output(f">waiting {seconds}s for {condition} [{condition()}]")
        async for _ in self.loop_for_duration(seconds):
            if condition():
                return True

        return False

    async def wait_for_messages(self, message_types: List, timeout: int):
        end_time = datetime.utcnow() + timedelta(seconds=timeout)
        while timeout > 0:
            try:
                e = await asyncio.wait_for(self.q.get(), timeout=timeout)
                if any([isinstance(e, t) for t in message_types]):
                    self.output(f"Got {e.event_type}")
                    return e
            except asyncio.TimeoutError:
                pass

            timeout = (end_time - datetime.utcnow()).total_seconds()

        return AbacuraMessage("timeout", "")

    @staticmethod
    async def loop_for_duration(seconds, tick=0.1):
        start_time: datetime = datetime.utcnow()

        while (datetime.utcnow() - start_time).total_seconds() < seconds:
            yield (datetime.utcnow() - start_time).total_seconds()
            await asyncio.sleep(tick)

    def send(self, message: str):
        self.output(f"[bold purple]{message}", markup=True)
        self.send(message)

    @event(trigger="lok.room")
    def got_room(self, message: RoomMessage):
        if self.worker and self.worker.state == WorkerState.RUNNING:
            self.q.put_nowait(message)

    @command
    def goa(self, destination: Room, avoid_home: bool = False):
        """Compute path to a room/location"""
        if self.worker:
            self.output("Stopping Current Navigation")

        self.worker = self.session.abacura.run_worker(self.navigate_async(destination, avoid_home),
                                                      group=self.session.name, name="nav_async",
                                                      exit_on_error=False, exclusive=False)
        self.add_ticker(0.1, self.check_worker, repeats=-1, name="check_worker")

    async def navigate_async(self, destination: Room, avoid_home: bool = False):
        self.output(f"Starting Navigation to {destination.vnum}")

        navigator = Navigator(self.world, self.pc, level=self.msdp.level, avoid_home=avoid_home)

        async with asyncio.timeout(60):
            self.send("look")

            nav_path = navigator.get_path_to_room(self.msdp.room_vnum, destination.vnum, avoid_vnums=set())
            self.output(f"Path {nav_path.get_simplified_path()}")

            while self.msdp.room_vnum != nav_path.destination.vnum:
                if not nav_path.destination:
                    self.output(f"[orange1]Unable to compute path to {destination.vnum}", markup=True)
                    return False

                e = await self.wait_for_messages([RoomMessage], 3)
                if e.event_type == 'timeout':
                    self.send("look")
                    continue

                if self.msdp.room_vnum not in self.world.rooms:
                    self.output(f"unknown room {self.msdp.room_vnum}, navigation halted")
                    return False

                if not nav_path.truncate_remaining_path(self.msdp.room_vnum):
                    self.session.output("LOST PATH - retrying")
                    nav_path = navigator.get_path_to_room(self.msdp.room_vnum, destination.vnum, avoid_vnums=set())
                    self.send("look")
                    continue

                for step in nav_path.steps:
                    if step.open and self.msdp.room_exits.get(step.exit.direction) != 'C':
                        continue

                    if step.vnum == self.msdp.room_vnum:
                        cmd = step.get_command()
                        self.send(cmd)

            self.output("[bold purple]Arrived!", markup=True)
            return True

