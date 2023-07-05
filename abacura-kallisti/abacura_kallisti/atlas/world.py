import re
import sqlite3
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from .room import ScannedRoom, Exit, Room
from .wilderness import WildernessGrid


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


class World:
    def __init__(self, db_filename: str):
        db_path = Path(db_filename).expanduser()

        self.rooms: Dict[str, Room] = {}
        self.wilderness_loaded: bool = False

        # temporary portals do not get persisted
        self.grid = WildernessGrid()
        self.db_conn = sqlite3.connect(db_path)
        self.db_conn.execute("PRAGMA journal_mode=WAL")
        self.create_tables()

        from datetime import datetime
        start_time = datetime.utcnow()
        self.load()
        self.load_time = (datetime.utcnow() - start_time).total_seconds()

    def del_exit(self, vnum: str, direction: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if direction not in room.exits:
            return

        del room.exits[direction]
        self._save_room(vnum)

    def set_exit(self, vnum: str, direction: str, door: str = '', to_vnum: str = None, commands: str = ''):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        exit = room.exits.get(direction, Exit(direction=direction, from_vnum=vnum))
        exit.door = door
        exit.commands = commands

        if to_vnum is not None:
            exit.to_vnum = to_vnum

        room.exits[direction] = exit

        self._save_room(vnum)

    def search(self, word: str) -> List[Room]:
        word = word.lower()
        result = []
        for r in self.rooms.values():
            if r.name.lower().find(word) >= 0:
                result.append(r)
        return result

    # def track_kill(self, vnum: str):
    #     if vnum in self.tracking:
    #         self.tracking[vnum].kills += 1

    def visited_room(self, area_name: str, name: str, vnum: str, terrain: str,
                     room_exits: Dict, scan_room: ScannedRoom):
        if area_name == 'The Wilderness':
            self.load_wilderness()

        # can't do much with a '?' vnum for now
        if vnum == '?':
            return

        if vnum in self.rooms:
            existing_room = self.rooms[vnum]
            existing_exits = {k: v for k, v in existing_room.exits.items() if not v.temporary}

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
        new_room = Room(area_name=area_name, vnum=vnum, name=name, terrain_name=terrain,
                        _exits=new_exits, bank=bank,
                        regen_hp=regen_hp, regen_mp=regen_mp, regen_sp=regen_sp, wild_magic=wild_magic,
                        silent=existing_room.silent, no_magic=existing_room.no_magic or no_magic,
                        no_recall=existing_room.no_recall or no_recall, set_recall=set_recall,
                        deathtrap=existing_room.deathtrap, peaceful=existing_room.peaceful,
                        last_visited=datetime.utcnow(), last_harvested=existing_room.last_harvested)

        self.rooms[vnum] = new_room
        self._save_room(vnum)

    def create_tables(self):

        sql_updates = [
            (1, "alter table exits add column commands"),
            (1, "update exits set commands = portal_method where portal_method != ''"),
            (1, """update exits set commands = portal_method || ' ' || portal where portal_method != ''
                               and portal_method not like '%down' and portal_method not like '%up'
                               and portal_method not like '%east' and portal_method not like '%west'
                               and portal_method not like '%north' and portal_method not like '%south'"""),
            (1, "alter table exits drop column portal"),
            (1, "alter table exits drop column portal_method"),
            (1, "create index exits_n1 on exits(to_vnum)"),
            (1, "alter table rooms drop column navigable"),
            (1, "alter table rooms add column last_visited"),
            (1, "alter table rooms add column last_harvested"),
            (1, "update rooms set last_visited = (select last_visited from room_tracking where room_tracking.vnum = rooms.vnum)"),
            (1, "update rooms set last_harvested = (select last_harvested from room_tracking where room_tracking.vnum = rooms.vnum)"),
            (2, "alter table rooms rename column terrain to terrain_name"),
            (2, "update rooms set terrain_name = 'Ocean' where vnum in ('87546', '87897', '88248', '88599', '88950', '89301')")
        ]

        max_sql_version = max([version for version, sql in sql_updates])
        schema_version = self.db_conn.execute("pragma schema_version").fetchall()[0][0]

        if schema_version == 0:
            # brand new db
            field_names = [f.name for f in fields(Exit) if not f.name.startswith("_")]
            sql = f"create table if not exists exits({','.join(field_names)}, PRIMARY KEY ({'from_vnum, direction'}))"
            self.db_conn.execute(sql)

            field_names = [f.name for f in fields(Room) if not f.name.startswith("_")]
            sql = f"create table if not exists rooms({','.join(field_names)}, primary key ({'vnum'}))"
            self.db_conn.execute(sql)

            self.db_conn.execute(f"pragma user_version={max_sql_version}")

            self.db_conn.commit()

        # Check if we need to run any sql updates to the db
        user_version_current = self.db_conn.execute("pragma user_version").fetchall()[0][0]
        if user_version_current >= max_sql_version:
            return

        for sql_version, sql in sql_updates:
            if sql_version > user_version_current:
                self.db_conn.execute(sql)
                user_version_new = sql_version

        self.db_conn.execute(f"pragma user_version = {max_sql_version}")
        self.db_conn.commit()

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
        room_fields = [getattr(room, pf) for pf in room.persistent_fields()]
        
        room_binds = ",".join("?" * len(room_fields))

        self.db_conn.execute("BEGIN TRANSACTION")
        self.db_conn.execute(f"INSERT OR REPLACE INTO rooms VALUES({room_binds})", room_fields)

        self.db_conn.execute(f"DELETE FROM exits WHERE from_vnum = ?", (vnum,))

        for room_exit in room.exits.values():
            if room_exit.temporary:
                continue
            exit_fields = [getattr(room_exit, pf) for pf in room_exit.persistent_fields()]
            exit_binds = ','.join('?' * len(exit_fields))
            self.db_conn.execute(f"INSERT INTO exits VALUES({exit_binds})", exit_fields)

        self.db_conn.commit()

    def load(self, where_clause: str = "where area_name != 'The Wilderness'"):
        cursor = self.db_conn.execute(f"select * from rooms {where_clause}")
        # field_names = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        for row in rows:
            # d = {name: value for name, value in zip(field_names, row)}
            new_room = Room(*row)
            self.rooms[new_room.vnum] = new_room

        # print(len(rows), "rooms loaded from db")

        sql = f"select e.* from exits e join rooms r on e.from_vnum = r.vnum {where_clause}"
        cursor = self.db_conn.execute(sql)
        rows = cursor.fetchall()

        for row in rows:
            new_exit = Exit(*row)
            if new_exit.from_vnum in self.rooms:
                self.rooms[new_exit.from_vnum].exits[new_exit.direction] = new_exit

        # print(len(rows), "exits loaded from db")

    def load_wilderness(self):
        if not self.wilderness_loaded:
            self.load("where area_name = 'The Wilderness'")
            self.wilderness_loaded = True
