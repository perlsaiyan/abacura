import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from abacura_kallisti.atlas.room import ScannedRoom
from abacura_kallisti.atlas.wilderness import WildernessGrid

import re


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
class KnownExit:
    direction: str = ''
    from_vnum: str = ''
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
class KnownRoom:
    vnum: str = ""
    name: str = ""
    terrain: str = ""
    area_name: str = ""
    exits: str = ""
    known_exits: Dict[str, KnownExit] = field(default_factory=dict)
    regen_hp: bool = False
    regen_mp: bool = False
    regen_sp: bool = False
    set_recall: bool = False
    peaceful: bool = False
    deathtrap: bool = False
    silent: bool = False
    wild_magic: bool = False
    narrow: bool = False
    no_magic: bool = False
    no_recall: bool = False
    navigable: bool = True


@dataclass(slots=True)
class RoomTracking:
    vnum: str = ""
    visited: bool = False
    last_harvested: Optional[datetime] = None
    last_visited: Optional[datetime] = None
    last_searched: Optional[datetime] = None
    kills: int = 0


class World:
    def __init__(self):
        self.rooms: Dict[str, KnownRoom] = {}
        self.tracking: Dict[str, RoomTracking] = {}
        self.visits_processed: int = 0
        self.temporary_portals: Dict[str, Dict[str, KnownExit]] = {}
        self.wilderness_loaded = False
        self.load()
        self.grid = WildernessGrid()

    def get_known_exits(self, vnum: str, exclude_temporary: bool = False) -> Dict[str, KnownExit]:
        if vnum not in self.rooms:
            return {}

        if vnum in ['?', '']: 
            return {}

        exits = self.rooms[vnum].known_exits.copy()
        if vnum in self.temporary_portals and not exclude_temporary:
            exits.update(self.temporary_portals[vnum])

        v = int(vnum)
        if v < 70000:
            return exits

        wilderness_exits = {}
        for direction, to_vnum in self.grid.get_exits(vnum).items():
            ke = KnownExit(direction, from_vnum=vnum, to_vnum=to_vnum)
            wilderness_exits[direction] = ke
 
        wilderness_exits.update(exits)
        return wilderness_exits

    def del_door(self, vnum: str, direction: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if direction not in room.known_exits:
            return

        del room.known_exits[direction]

    def set_door(self, vnum: str, direction: str, door: str, to_vnum: str = None):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if direction not in room.known_exits:
            return

        room.known_exits[direction].door = door
        if to_vnum is not None:
            room.known_exits[direction].to_vnum = to_vnum

    def add_portal(self, vnum: str, name: str, method: str, to_vnum: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        exits = room.known_exits
        new_exit = KnownExit(direction=name, from_vnum=vnum, to_vnum=to_vnum, portal=name, portal_method=method)
        exits[name] = new_exit

    def delete_portal(self, vnum: str, name: str):
        if vnum not in self.rooms:
            return

        room = self.rooms[vnum]
        if name in room.known_exits:
            del room.known_exits[name]

    def add_temp_exit(self, vnum: str, name: str, method: str, to_vnum: str):
        if vnum not in self.temporary_portals:
            self.temporary_portals[vnum] = {}

        temp_portals = self.temporary_portals[vnum]
        if name not in temp_portals:
            temp_portals[name] = KnownExit(name, vnum, to_vnum, name, method)

    def delete_room(self, vnum: str):
        if vnum not in self.rooms:
            return
        del self.rooms[vnum]

    def search(self, word: str) -> List[KnownRoom]:
        word = word.lower()
        result = []
        for r in self.rooms.values():
            if r.name.lower().find(word) >= 0:
                result.append(r)
        return result

    def track_kill(self, vnum: str):
        if vnum in self.tracking:
            self.tracking[vnum].kills += 1

    def visited_room(self, area_name: str, name: str, vnum: str, terrain: str, room_exits: Dict, room: ScannedRoom):
        if not self.wilderness_loaded and area_name == 'The Wilderness':
            self.load_wilderness()

        self.visits_processed += 1
        if (self.visits_processed % 100) == 0:
            print("Saving room tracking info")
            self.save_tracking()

        # can't do much with a '?' vnum for now
        if vnum == '?':
            return

        self.get_tracking(room.room_vnum).last_visited = datetime.utcnow()
        self.get_tracking(room.room_vnum).visited = True

        if vnum in self.rooms:
            existing_room = self.rooms[vnum]
            existing_exits = self.get_known_exits(vnum, exclude_temporary=True)
        else:
            existing_room = KnownRoom()
            existing_exits = {}

        # room_exits = tintin.parse_table(exits)
        known_exits = existing_exits

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
                e = KnownExit(direction=d, from_vnum=vnum, to_vnum=to_vnum, locks=locks, closes=closes)

            known_exits[d] = e

        regen_hp = room and room.room_header.find("RegenHp") >= 0
        regen_mp = room and room.room_header.find("RegenMp") >= 0
        regen_sp = room and room.room_header.find("RegenSp") >= 0
        wild_magic = room and room.room_header.find('Wild Magic') >= 0
        no_magic = room and room.room_header.find('NoMagic') >= 0
        set_recall = room and room.room_header.find('SetRecall') >= 0
        no_recall = room and room.room_header.find('Warded') >= 0
        terrain = strip_ansi_codes(terrain)

        # TODO: Should we really be creating a new room, or just updating the existing one with new values
        known_room = KnownRoom(area_name=area_name, vnum=vnum, name=name, terrain=terrain,
                               known_exits=known_exits,
                               regen_hp=regen_hp, regen_mp=regen_mp, regen_sp=regen_sp, wild_magic=wild_magic,
                               silent=existing_room.silent, no_magic=existing_room.no_magic or no_magic,
                               no_recall=existing_room.no_recall or no_recall, set_recall=set_recall,
                               deathtrap=existing_room.deathtrap, peaceful=existing_room.peaceful)

        self.rooms[vnum] = known_room

    def get_tracking(self, vnum: str) -> RoomTracking:
        if vnum not in self.tracking:
            self.tracking[vnum] = RoomTracking()
        return self.tracking[vnum]

    @staticmethod
    def load_data_pickle(filename: str) -> Optional[Dict]:
        try:
            with open(filename, 'rb') as pickle_file:
                return pickle.Unpickler(pickle_file).load()
                # return RenamingUnpickler(pickle_file).load()
        except FileNotFoundError:
            return None

    def load_wilderness(self):
        # start = datetime.utcnow()
        if wild := self.load_data_pickle('rooms_wilderness.pkl'):
            self.rooms.update(wild)

        if track := self.load_data_pickle('room_tracking_wilderness.pkl'):
            self.tracking.update(track)

        # print("Wilderness rooms loaded in %5.3fs" % (datetime.utcnow() - start).total_seconds())
        self.wilderness_loaded = True

    def load(self):
        if rooms := self.load_data_pickle("rooms_non_wilderness.pkl"):
            self.rooms = rooms

        # with open(config.DIR_DATA + "/" + "rooms_non_wilderness.pkl_slots", 'rb') as f:
        #     self.rooms_slots = pickle.Unpickler(f).load()

        if tracking := self.load_data_pickle("room_tracking_non_wilderness.pkl"):
            self.tracking = tracking

    def save(self):
        self.save_tracking()
        self.save_rooms()

    @staticmethod
    def save_object_with_backup(obj, filename: str):
        file = Path(filename)
        temp = Path(filename + ".tmp")
        backup = Path(filename + ".bak")
        # write to a temporary file in case we get killed while writing, prevent corrupting the file

        if temp.exists():
            temp.unlink()

        with open(temp, 'wb') as pickle_file:
            pickle.dump(obj, pickle_file)

        if backup.exists():
            backup.unlink()

        if file.exists():
            file.rename(backup)

        temp.rename(file)

    def save_tracking(self):
        # self.save_object_with_backup(self.tracking, 'room_tracking.pkl')

        wilderness_vnums = {r.vnum for r in self.rooms.values() if r.area_name == 'The Wilderness'}
        wilderness = {k: v for k, v in self.tracking.items() if v.vnum in wilderness_vnums}

        if len(wilderness) > 100 and self.wilderness_loaded:
            self.save_object_with_backup(wilderness, 'room_tracking_wilderness.pkl')

        non_wilderness = {k: v for k, v in self.tracking.items() if v.vnum not in wilderness_vnums}
        self.save_object_with_backup(non_wilderness, 'room_tracking_non_wilderness.pkl')

    def save_rooms(self):
        # self.save_object_with_backup(self.rooms, 'rooms.pkl')

        wilderness = {k: v for k, v in self.rooms.items() if v.area_name == 'The Wilderness'}
        if len(wilderness) > 100 and self.wilderness_loaded:
            self.save_object_with_backup(wilderness, 'rooms_wilderness.pkl')

        non_wilderness = {k: v for k, v in self.rooms.items() if v.area_name != 'The Wilderness'}

        # with open(config.DIR_DATA + "/" + "rooms_non_wilderness.pkl_slots", 'wb') as f:
        #     KnownExit.__slots__ = KnownExit.slots
        #     pickle.dump(self.rooms, f)

        self.save_object_with_backup(non_wilderness, 'rooms_non_wilderness.pkl')

