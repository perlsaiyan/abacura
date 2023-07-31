import importlib

from rich.text import Text

import abacura.utils.renderables as tblt
from abacura.plugins import command
from abacura.plugins.events import event, AbacuraMessage
from abacura.utils.renderables import tabulate, AbacuraPropertyGroup, AbacuraPanel, Group, OutputColors, Style
from abacura_kallisti.atlas.messages import MapUpdateMessage, MapUpdateRequest
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.atlas.world import Room
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.plugins.scripts.travel import TravelStatus


class WorldController(LOKPlugin):
    """Commands to manipulate rooms and exits in the world database"""

    def __init__(self):
        super().__init__()
        self.wild_grid = WildernessGrid()
        importlib.reload(tblt)
        self.traveling = False

    def dispatch_map_message(self, vnum: str):
        room = self.world.rooms.get(vnum, None)
        msg = MapUpdateMessage(start_room=room, world=self.world, current_vnum=vnum, traveling=self.traveling)
        self.dispatch(msg)

    @event("core.msdp.ROOM_VNUM")
    def update_room_vnum(self, message: AbacuraMessage):
        self.dispatch_map_message(message.value)

    @event(TravelStatus.event_type)
    def update_travel_status(self, message: TravelStatus):
        self.traveling = message.steps_remaining > 0
        self.dispatch_map_message(self.msdp.room_vnum)

    @event(MapUpdateRequest.event_type)
    def map_update_request(self, _message: MapUpdateRequest):
        self.dispatch_map_message(self.msdp.room_vnum)

    def get_table_of_exits(self, vnum: str):
        exits = []
        for e in self.world.rooms[vnum].exits.values():
            known = e.to_vnum in self.world.rooms
            visited = False
            terrain = ""
            if known:
                to_room = self.world.rooms[e.to_vnum]
                visited = to_room.last_visited not in ['', None]
                terrain = to_room.terrain_name

            exits.append((e.direction, e.to_vnum, e.door, e.commands,
                          bool(e.closes), bool(e.locks), bool(e.deathtrap), known, visited, terrain))

        exits = sorted(exits)
        caption = ""
        if vnum == self.msdp.room_vnum:
            caption = f" MSDP_EXITS: {str(self.msdp.room_exits)}"

        return tabulate(exits, caption=caption, headers=["Direction", "_To", "Door", "Commands", "Closes",
                                                         "Locks", "Deathtrap", "Known", "Visited", "Terrain"],
                        title="Exits")

    @command(name="room")
    def room_command(self, location: Room = None, delete: bool = False,
                     silent: bool = False, deathtrap: bool = False, peaceful: bool = False,
                     norecall: bool = False, nomagic: bool = False):
        """
        Display information about a room

        :param location: A room vnum or location name
        :param delete: Will delete the room
        :param silent: Toggle silent flag
        :param deathtrap: Toggle deathtrap flag
        :param peaceful: Toggle peaceful flag
        :param norecall: Toggle no_recall flag
        :param nomagic: Toggle no_magic flag
        """

        if location is None:
            if self.msdp.room_vnum not in self.world.rooms:
                self.session.show_error(f"Unknown room {self.msdp.room_vnum}")
                return

            location = self.world.rooms[self.msdp.room_vnum]

        if silent:
            location.silent = not location.silent

        if deathtrap:
            location.deathtrap = not location.deathtrap

        if peaceful:
            location.peaceful = not location.peaceful

        if nomagic:
            location.no_magic = not location.no_magic

        if norecall:
            location.no_recall = not location.no_recall

        if silent or deathtrap or peaceful or nomagic or norecall:
            txt = Text.assemble(
                ("Flag toggled\n\n", OutputColors.success),
                ("Flags: ", Style(color=OutputColors.field, bold=True)),
                (str(self.get_room_flags(location)), OutputColors.value))
            self.output(AbacuraPanel(txt, title=f"Room [ {location.vnum} ] Flags"))
            self.world.save_room(location.vnum)
            return

        properties = {"Area": location.area_name,
                      "Terrain": location.terrain_name,
                      "Weight": location.terrain.weight,
                      "Flags": self.get_room_flags(location),
                      "Visited": location.last_visited
                      }

        if location.area_name == 'The Wilderness':
            x, y = self.wild_grid.get_point(location.vnum)
            ox, oy = self.wild_grid.get_orienteering_point(location.vnum)
            properties["x, y"] = f"{x}, {y} [{ox}, {oy}]"
            properties["Harvested"] = location.last_harvested

        location_names = [f"{a.category}.{a.name}" for a in self.locations.get_locations_for_vnum(location.vnum)]
        if len(location_names) > 0:
            properties["Locations"] = ', '.join(location_names)

        pview = AbacuraPropertyGroup(properties)
        table = self.get_table_of_exits(location.vnum)
        panel = AbacuraPanel(Group(pview, Text(), table), title=f"[ {location.vnum} ] - {location.name}")
        self.output(panel, highlight=True)

        if delete:
            self.world.delete_room(location.vnum)
            txt = Text(f"Room [ {location.vnum} ] deleted", OutputColors.success)
            self.output(AbacuraPanel(txt, title="Delete Room"))

    @staticmethod
    def get_room_flags(room: Room) -> str:
        flags = ['wild_magic', 'silent', 'set_recall', 'no_recall', 'no_magic', 'narrow',
                 'peaceful', 'deathtrap', 'regen_hp', 'regen_mp', 'regen_sp', 'bank']
        flags = [f.replace('_', ' ') for f in flags if getattr(room, f, False)]
        return ','.join(flags)

    # @command()
    # def roomflags(self, peaceful: bool = False, silent: bool = False,
    #               no_recall: bool = False, no_magic: bool = False, wild_magic: bool = False,
    #               narrow: bool = False):
    #     """Display flags for a room"""
    #     if self.msdp.room_vnum not in self.world.rooms:
    #         raise CommandError('Unknown room [%s]' % self.msdp.room_vnum)
    #
    #     room = self.world.rooms[self.msdp.room_vnum]
    #     # If the parameter is true, toggle the room value.  ^ is an XOR operation for the toggle.
    #     room.peaceful = room.peaceful ^ peaceful
    #     room.silent = room.silent ^ silent
    #     room.no_recall = room.no_recall ^ no_recall
    #     room.no_magic = room.no_magic ^ no_magic
    #     room.wild_magic = room.wild_magic ^ wild_magic
    #     room.narrow = room.narrow ^ narrow
    #
    #     self.session.output("[%s] %s" % (room.vnum, room.name))
    #     room = self.world.rooms[room.vnum]
    #     self.session.output("Flags: %s" % self.get_room_flags(room))

    @command()
    def exits(self, direction: str = '', to_vnum: str = '', _door: str = '', _commands: str = '', delete: bool = False):
        """View and modify exits in current room

        :param direction: Direction of exit to view or modify
        :param delete: Remove exit
        :param to_vnum: Set to_vnum of exit
        :param _door: Set name of door to open/close
        :param _commands: Set multiple commands to use, separated by ;
        """

        vnum = self.msdp.room_vnum

        if vnum not in self.world.rooms:
            self.session.show_error(f"Unknown room [ {vnum} ]")
            return

        if not direction:
            tbl = self.get_table_of_exits(vnum)
            tbl.title = ""
            self.session.output(AbacuraPanel(tbl, title=f"Exits for room [ {vnum} ]"))
            return

        if delete:
            self.world.del_exit(vnum, direction)
            txt = Text(f"Deleted [ {vnum} ] {direction}")
            tbl = self.get_table_of_exits(vnum)
            self.output(AbacuraPanel(Group(txt, Text(), tbl), title="Delete Exit"), highlight=True)
            return

            # #exits goliath 60254 --commands="visit goliath"

        if _door != '' or _commands != '' or to_vnum != '':
            self.world.set_exit(vnum, direction, door=_door, to_vnum=to_vnum, commands=_commands)
            txt = Text(f"Set [ {vnum} ] {direction} to={to_vnum}, door={_door}, commands={_commands}")
            tbl = self.get_table_of_exits(vnum)
            self.output(AbacuraPanel(Group(txt, Text(), tbl), title="Set Exit"), highlight=True)
            return

        room = self.world.rooms[vnum]
        if direction not in room.exits:
            self.session.show_error(f"Unknown direction {direction} for room [ {vnum} ]")
            return

        e = room.exits[direction]

        pview = AbacuraPropertyGroup(e)
        self.output(AbacuraPanel(pview, title=f"Room [ {vnum} ] - {direction}"), highlight=True)

    @command
    def sql(self, query: str, _max_rows: int = 100):
        """
        Run a sql query against the world database

        :param query: The sql query to run
        :param _max_rows: Maximum rows to display
        """
        try:
            cursor = self.world.db_conn.execute(query)
        except Exception as e:
            self.session.show_exception(e)
            return

        if not cursor.description:
            self.output("executed")
            return

        rows = list(cursor.fetchmany(_max_rows))

        pview = AbacuraPropertyGroup({"sql": query}, title="Query")

        if len(rows) == 0:
            results = Text.assemble(("Results\n\n", OutputColors.section), ("No rows returned", ""))
        else:
            headers = [c[0] for c in cursor.description]
            caption = f" {min(len(rows),_max_rows)}/{len(rows)} rows shown"
            results = tabulate(rows, headers=headers, title="Results", caption=caption, expand=True)

        self.output(AbacuraPanel(Group(pview, Text(), results), "SQL Query", expand=True))
