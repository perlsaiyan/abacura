import re
import sqlite3
from dataclasses import dataclass, field, fields, astuple
from datetime import datetime
from typing import List, Dict, Optional

from atlas.room import ScannedRoom
from atlas.wilderness import WildernessGrid


# TODO: Use the abacura methods for strip_ansi_codes
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def strip_ansi_codes(s: str) -> str:
    """
    Remove ansi color codes / escape sequences from a string
    :param s: The original string with color codes
    :return: A string with the color codes stripped
    """
    # ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', s)


@dataclass(slots=True)
class Exit:
    from_vnum: str = ''
    direction: str = ''
    to_vnum: str = ''
    portal: str = ''
    portal_method: str = ''
    door: str = ''
    closes: bool = False
    locks: bool = False
    key_name: str = ''
    weight: int = 0
    max_level: int = 100
    min_level: int = 0
    deathtrap: bool = False


@dataclass(slots=True)
class Room:
    vnum: str = ""
    name: str = ""
    terrain: str = ""
    area_name: str = ""
    regen_hp: bool = False
    regen_mp: bool = False
    regen_sp: bool = False
    set_recall: bool = False
    peaceful: bool = False
    deathtrap: bool = False
    silent: bool = False
    wild_magic: bool = False
    bank: bool = False
    narrow: bool = False
    no_magic: bool = False
    no_recall: bool = False
    navigable: bool = True
    # exits should be last to make the simple db query work
    exits: Dict[str, Exit] = field(default_factory=dict)


@dataclass(slots=True)
class RoomTracking:
    vnum: str = ""
    last_harvested: Optional[datetime] = None
    last_visited: Optional[datetime] = None
    last_searched: Optional[datetime] = None
    kills: int = 0


class World:
    def __init__(self, db_filename: str):
        self.rooms: Dict[str, Room] = {}
        self.tracking: Dict[str, RoomTracking] = {}

        # temporary portals do not get persisted
        self.temporary_portals: Dict[str, Dict[str, Exit]] = {}
        self.grid = WildernessGrid()

        self.db_conn = sqlite3.connect(db_filename)
        self.db_conn.execute("PRAGMA journal_mode=WAL")
        self.create_tables()

        self.load()

    def get_exits(self, vnum: str, exclude_temporary: bool = False) -> Dict[str, Exit]:
        if vnum not in self.rooms:
            return {}

        if vnum in ['?', '']: 
            return {}

        exits = self.rooms[vnum].exits.copy()
        if vnum in self.temporary_portals and not exclude_temporary:
            exits.update(self.temporary_portals[vnum])

        v = int(vnum)
        if v < 70000:
            return exits

        wilderness_exits = {}
        for direction, to_vnum in self.grid.get_exits(vnum).items():
            e = Exit(direction=direction, from_vnum=vnum, to_vnum=to_vnum)
            wilderness_exits[direction] = e
 
        wilderness_exits.update(exits)
        return wilderness_exits

    def del_door(self, vnum: str, direction: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if direction not in room.exits:
            return

        del room.exits[direction]

    def set_door(self, vnum: str, direction: str, door: str, to_vnum: str = None):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if direction not in room.exits:
            return

        room.exits[direction].door = door
        if to_vnum is not None:
            room.exits[direction].to_vnum = to_vnum

        self._save_room(vnum)

    def add_portal(self, vnum: str, name: str, method: str, to_vnum: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        exits = room.exits
        new_exit = Exit(direction=name, from_vnum=vnum, to_vnum=to_vnum, portal=name, portal_method=method)
        exits[name] = new_exit

        self._save_room(vnum)

    def delete_portal(self, vnum: str, name: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if name in room.exits:
            del room.exits[name]

        self._save_room(vnum)

    def add_temp_exit(self, vnum: str, name: str, method: str, to_vnum: str):
        if vnum not in self.temporary_portals:
            self.temporary_portals[vnum] = {}

        temp_portals = self.temporary_portals[vnum]
        if name not in temp_portals:
            temp_portals[name] = Exit(name, vnum, to_vnum, name, method)

    def search(self, word: str) -> List[Room]:
        word = word.lower()
        result = []
        for r in self.rooms.values():
            if r.name.lower().find(word) >= 0:
                result.append(r)
        return result

    def track_kill(self, vnum: str):
        if vnum in self.tracking:
            self.tracking[vnum].kills += 1

    def visited_room(self, area_name: str, name: str, vnum: str, terrain: str, room_exits: Dict, scan_room: ScannedRoom):

        # can't do much with a '?' vnum for now
        if vnum == '?':
            return

        self.get_tracking(scan_room.room_vnum).last_visited = datetime.utcnow()

        if vnum in self.rooms:
            existing_room = self.rooms[vnum]
            existing_exits = self.get_exits(vnum, exclude_temporary=True)
        else:
            existing_room = Room()
            existing_exits = {}

        new_exits = existing_exits.copy()

        for d, to_vnum in room_exits.items():
            locks = to_vnum == 'L'
            closes = to_vnum in ['L', 'C']
            to_vnum_check = ''

            if to_vnum and to_vnum not in ['C', 'L', '?']:
                # only update existing exit vnum if we didn't see a '?' here
                to_vnum_check = to_vnum

            if d in existing_exits:
                e = existing_exits[d]
                if to_vnum_check == '' and e.to_vnum != '':
                    to_vnum_check = e.to_vnum

                # keep existing lock/closes flags
                e.locks = locks or e.locks
                e.closes = closes or e.closes
                e.to_vnum = to_vnum_check
                # e = replace(e, locks=locks, closes=closes, to_vnum=to_vnum_check)
            else:
                e = Exit(direction=d, from_vnum=vnum, to_vnum=to_vnum, locks=locks, closes=closes)

            new_exits[d] = e

        regen_hp = scan_room and scan_room.room_header.find("RegenHp") >= 0
        regen_mp = scan_room and scan_room.room_header.find("RegenMp") >= 0
        regen_sp = scan_room and scan_room.room_header.find("RegenSp") >= 0
        wild_magic = scan_room and scan_room.room_header.find('Wild Magic') >= 0
        no_magic = scan_room and scan_room.room_header.find('NoMagic') >= 0
        set_recall = scan_room and scan_room.room_header.find('SetRecall') >= 0
        no_recall = scan_room and scan_room.room_header.find('Warded') >= 0
        bank = scan_room and scan_room.room_header.find('Bank') >= 0
        terrain = strip_ansi_codes(terrain)

        # TODO: Should we really be creating a new room, or just updating the existing one with new values
        new_room = Room(area_name=area_name, vnum=vnum, name=name, terrain=terrain,
                        exits=new_exits, bank=bank,
                        regen_hp=regen_hp, regen_mp=regen_mp, regen_sp=regen_sp, wild_magic=wild_magic,
                        silent=existing_room.silent, no_magic=existing_room.no_magic or no_magic,
                        no_recall=existing_room.no_recall or no_recall, set_recall=set_recall,
                        deathtrap=existing_room.deathtrap, peaceful=existing_room.peaceful)

        self.rooms[vnum] = new_room
        self._save_room(vnum)

    def get_tracking(self, vnum: str) -> RoomTracking:
        if vnum not in self.tracking:
            self.tracking[vnum] = RoomTracking()
        return self.tracking[vnum]

    def create_tables(self):
        field_names = [f.name for f in fields(Exit)]
        sql = f"create table if not exists exits({','.join(field_names)}, PRIMARY KEY ({'from_vnum, direction'}))"
        self.db_conn.execute(sql)

        field_names = [f.name for f in fields(Room) if f.name != "exits"]
        sql = f"create table if not exists rooms({','.join(field_names)}, primary key ({'vnum'}))"
        self.db_conn.execute(sql)

        field_names = [f.name for f in fields(RoomTracking)]
        sql = f"create table if not exists room_tracking({','.join(field_names)}, primary key ({'vnum'}))"
        self.db_conn.execute(sql)

    def delete_room(self, vnum: str):
        if vnum in self.rooms:
            del self.rooms[vnum]

        self.db_conn.execute("delete from exits where from_vnum = ?", vnum)
        self.db_conn.execute("delete from exits where to_vnum = ?", vnum)
        self.db_conn.execute("delete from room_tracking where vnum = ? ", vnum)
        self.db_conn.execute("delete from rooms where vnum = ? ", vnum)

    def _save_room(self, vnum: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        room_fields = [v for v in astuple(room) if type(v) != dict]
        
        room_binds = ",".join("?" * len(room_fields))

        self.db_conn.execute("BEGIN TRANSACTION")
        self.db_conn.execute(f"INSERT OR REPLACE INTO rooms VALUES({room_binds})", room_fields)

        if vnum in self.tracking:
            trk = self.tracking[vnum]
            trk_fields = astuple(trk)
            trk_binds = ",".join("?" * len(trk_fields))

            self.db_conn.execute(f"INSERT OR REPLACE INTO room_tracking VALUES({trk_binds})", trk_fields)

        for room_exit in room.exits.values():
            exit_fields = astuple(room_exit)
            exit_binds = ",".join("?" * len(exit_fields))
            self.db_conn.execute(f"INSERT OR REPLACE INTO exits VALUES({exit_binds})", exit_fields)

        self.db_conn.commit()

    def load(self):

        cursor = self.db_conn.execute(f"select * from rooms")
        # field_names = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        for row in rows:
            # d = {name: value for name, value in zip(field_names, row)}
            new_room = Room(*row)
            self.rooms[new_room.vnum] = new_room

        # print(len(rows), "rooms loaded from db")

        cursor = self.db_conn.execute(f"select * from room_tracking")
        # field_names = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        for row in rows:
            # d = {name: value for name, value in zip(field_names, row)}
            new_trk = RoomTracking(*row)
            self.tracking[new_trk.vnum] = new_trk


        cursor = self.db_conn.execute(f"select e.* from exits e join rooms r on e.from_vnum = r.vnum")
        rows = cursor.fetchall()

        for row in rows:
            new_exit = Exit(*row)
            if new_exit.from_vnum in self.rooms:
                self.rooms[new_exit.from_vnum].exits[new_exit.direction] = new_exit

        # print(len(rows), "exits loaded from db")
