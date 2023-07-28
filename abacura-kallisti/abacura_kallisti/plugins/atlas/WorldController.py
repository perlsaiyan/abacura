import importlib

from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

import abacura.utils.tabulate as tblt
from abacura.plugins import command
from abacura.plugins.events import event, AbacuraMessage
from abacura.utils.tabulate import tabulate
from abacura_kallisti.atlas.messages import MapUpdateMessage, MapUpdateRequest
from abacura_kallisti.atlas.wilderness import WildernessGrid
from abacura_kallisti.atlas.world import Room
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.plugins.scripts.travel import TravelStatus


class WorldController(LOKPlugin):

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
            caption = f"MSDP_EXITS: {str(self.msdp.room_exits)}"

        return tabulate(exits, caption=caption, caption_justify="left",
                        headers=["Direction", "_To", "Door", "Commands", "Closes",
                                 "Locks", "Deathtrap", "Known", "Visited", "Terrain"])

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
                self.output(f"[bright red]Unknown room {self.msdp.room_vnum}", markup=True)
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
            self.output(f"[orange1] Toggle room flag", markup=True)
            self.world.save_room(location.vnum)

        text = Text()

        text.append(f"[{location.vnum}] {location.name}\n\n", style="bold magenta")
        text.append(f"     Area: {location.area_name}\n")

        terrain = location.terrain
        text.append(f"  Terrain: {location.terrain_name} [{terrain.weight}]\n")
        text.append(f"    Flags: {self.get_room_flags(location)}\n")
        text.append(f"  Visited: {location.last_visited}\n")

        if location.area_name == 'The Wilderness':
            x, y = self.wild_grid.get_point(location.vnum)
            ox, oy = self.wild_grid.get_orienteering_point(location.vnum)
            text.append(f"     x, y: {x}, {y} [{ox}, {oy}]\n")
            text.append(f"Harvested: {location.last_harvested}\n")

        location_names = [f"{a.category}.{a.name}" for a in self.locations.get_locations_for_vnum(location.vnum)]
        if len(location_names) > 0:
            text.append(f"Locations: {', '.join(location_names)}\n")

        text.highlight_regex(r"[a-zA-Z]+:", style="bold")

        table = self.get_table_of_exits(location.vnum)
        group = Group(text, table)
        panel = Panel(group)
        self.output(panel, highlight=True)

        if delete:
            self.world.delete_room(location.vnum)
            self.session.output("\n[orange1] ROOM DELETED\n", markup=True)

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

        :direction Direction of exit to view or modify
        :delete Remove exit
        :destination Set to_vnum of exit
        :_door Set name of door to open/close
        :_commands Set multiple commands to use, separated by ;

        """

        vnum = self.msdp.room_vnum

        if vnum not in self.world.rooms:
            self.session.output(f"[orange1][italic]Unknown room [{vnum}]", highlight=True, markup=True)
            return

        if not direction:
            self.session.output(self.get_table_of_exits(vnum))
            return

        if delete:
            self.world.del_exit(vnum, direction)
            self.session.output(f"Deleted [{vnum}] {direction}", highlight=True)
            self.session.output(self.get_table_of_exits(vnum))
            return

            # #exits goliath 60254 --commands="visit goliath"

        if _door != '' or _commands != '' or to_vnum != '':
            self.world.set_exit(vnum, direction, door=_door, to_vnum=to_vnum, commands=_commands)
            self.output(f"Set [{vnum}] {direction} to={to_vnum}, door={_door}, commands={_commands}", highlight=True)
            self.session.output(self.get_table_of_exits(vnum))
            return

        room = self.world.rooms[vnum]
        if direction not in room.exits:
            self.session.output(f"[orange1]Unknown direction {direction} for room [{vnum}]", markup=True)
            return
        e = room.exits[direction]
        properties = [(name, getattr(e, name)) for name in sorted(e.__slots__)]

        tbl = tabulate(properties, headers=("Property", "_Value"),
                       title=f"\n[{vnum}] {direction}", title_justify="left")
        self.output(tbl)

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
            self.session.show_exception(str(e), e)
            return

        if not cursor.description:
            self.output("executed")
            return

        title_style = Style(bgcolor="#000040", color="bright_white", bold=True)
        caption_style = Style(bgcolor="#000040", color="white")
        header_style = Style(bgcolor="#000040", color="bright_white")
        border_style = Style(bgcolor="#000040", color="#CCCCCC")
        s1 = Style(bgcolor="#101020", color="white")
        s2 = Style(bgcolor="#202040", color="white")
        rows = list(cursor.fetchmany(_max_rows))

        if len(rows) == 0:
            self.output(Panel(Text("No rows returned")))
            return

        headers = [c[0] for c in cursor.description]

        title = f"SQL: {query}"
        caption = f" Showing first {_max_rows} rows"

        tbl = tabulate(rows, headers=headers,
                       title=title, title_justify="left", title_style=title_style,
                       caption=caption, caption_justify="left", caption_style=caption_style,
                       row_styles=[s1, s2], header_style=header_style, border_style=border_style)
        #
        #
        # for i, column in enumerate(cursor.description):
        #     c = Counter([type(row[i]) for row in rows])
        #     column_types.append(c.most_common(1)[0][0])
        #     justify = "left"
        #     if column_types[i] in (int, 'int', float, 'float'):
        #         justify = "right"
        #     tbl.add_column(column[0], justify=justify)
        #     tbl.add
        #
        # for row in rows:
        #     new_row = []
        #     for i, v in enumerate(row):
        #         if column_types[i] in (float, 'float'):
        #             new_row.append(format(v, "6.3f"))
        #         else:
        #             new_row.append(str(v))
        #
        #     tbl.add_row(*new_row)

        self.output(Panel(tbl, style=border_style))
