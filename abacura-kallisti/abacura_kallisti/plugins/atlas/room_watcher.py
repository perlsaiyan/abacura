import re
import dataclasses
from typing import List, Optional
import os
import unicodedata
import tomlkit

from rich.panel import Panel
from rich.text import Text

# from atlas.known_areas import KNOWN_AREAS
from abacura.mud import OutputMessage
from abacura.plugins import action
from abacura.plugins.events import event, AbacuraMessage
from abacura_kallisti.atlas import encounter, item
from abacura_kallisti.atlas.room import ScannedRoom, RoomMessage
from abacura_kallisti.atlas.world import strip_ansi_codes
from abacura_kallisti.mud.area import Area
from abacura_kallisti.mud.mob import Mob
from abacura_kallisti.plugins import LOKPlugin

item_re = re.compile(r'(\x1b\[0m)?\x1b\[0;37m[^\x1b ]')
item_count_re = re.compile(r'\((\d+)\) $')

class RoomWatcher(LOKPlugin):

    def __init__(self):
        super().__init__()

        self.scanned_room: Optional[ScannedRoom] = None

        self.re_room_nocompass = re.compile(r"^.* (\[ [ NSWEUD<>v^\|\(\)\[\]]* \] *$)")
        self.re_room_compass = re.compile(r".* \|")
        self.re_room_here = re.compile(r"^Here +- ")

        self.re_player = re.compile(r"\x1b\[1;33m(\w+)")  # yellow
        self.re_mob_count = re.compile(r"\[(\d+)\]")
        self.re_corpse_count = re.compile(r"\((\d+)\)")

        self.flags = ['corpse', 'resting', 'incapacitated', 'sitting', 'lying', 'paralyzed', 'stunned', 'alert',
                      'ranged', 'mortally wounded', 'fighting YOU', 'fighting', 'sneaking', 'evil', 'good', 'grim ward',
                      'fireshield', 'acidshield', 'iceshield', 'shockshield', 'blur', 'wraith', 'sanc']
        self.flag_checks = [" %s " % f for f in self.flags]
        self.flag_checks += [" %s." % f for f in self.flags]

    @action("^Not here!")
    def no_magic(self):
        if self.msdp.room_vnum in self.world.rooms:
            r = self.world.rooms[self.msdp.room_vnum]
            if not r.no_magic or not r.no_recall:
                r.no_magic = True
                r.no_recall = True
                self.output(f'[orange1]Marked room no recall/magic [{r.vnum}]', markup=True)
                self.world.save_room(r.vnum)

    @action("^Your lips move,* but no sound")
    def silent(self):
        if self.msdp.room_vnum in self.world.rooms:
            r = self.world.rooms[self.msdp.room_vnum]
            if not r.silent:
                r.silent = True
                self.output(f'[orange1]Marked room silent [{r.vnum}]', markup=True)
                self.world.save_room(r.vnum)

    # @lru_cache(maxsize=1024)
    def match_wilderness(self, line, stripped):
        magenta: int = line.find("\x1b[1;35m")
        starts_with_magenta = (0 <= magenta < 5)

        return (starts_with_magenta and len(stripped) <= 40) or self.match_room(line, stripped)

    # @lru_cache(maxsize=8192)
    def match_room(self, line: str, stripped: str) -> bool:
        contains_bold_magenta = (line.find("\x1b[1;35m") >= 0)
        room_matched1 = self.re_room_nocompass.match(stripped) is not None
        room_matched2 = self.re_room_compass.match(stripped) is not None
        here_matched = self.re_room_here.match(stripped) is not None
        no_exits = stripped.find("[ No exits! ]") > 0
        return contains_bold_magenta and (room_matched1 or room_matched2 or here_matched or no_exits)

    # @lru_cache(maxsize=512)
    def get_mob_re_for_area(self, area_name: str) -> List:
        if area_name == self.room.area.name:
            mobs = self.room.area.mobs
            names = [mob.name for mob in mobs if mob.starts_with == '']

            wildcard = ".*?" if self.room.area.greedy_match else ".*"

            # In is for Thalos golems
            grp = "|".join(names)
            mob_re = "^(You see )*(A|The|This|An|a|the|an|In|in|His|There is an|,)%s (%s)[ .,']" % (wildcard, grp)
            compiled_mob_re = re.compile(mob_re)
            self.debuglog("mob re %s" % mob_re)
            # for mobs with fancy names
            start_names = [mob.starts_with for mob in mobs if mob.starts_with != '']
            start_re = "^(%s)[, ]" % "|".join(start_names)
            compiled_start_re = re.compile(start_re, flags=re.IGNORECASE)
            # self.session.debug("starts re %s" % start_re, show=True)

            return [compiled_mob_re, compiled_start_re]
        return []

    # @lru_cache(maxsize=1024)
    def get_mob_name(self, area_name: str, stripped: str) -> Optional[str]:
        mob_re_list = self.get_mob_re_for_area(area_name)
        # self.session.debug('area %s stripped %s' % (area_name, stripped), show=True )

        if len(mob_re_list) == 0:
            return None

        for mob_re in mob_re_list:
            m = mob_re.match(stripped)
            if m is not None:
                # self.session.debug('M: %s' % m.groups()[-1], show=True)
                return m.groups()[-1]

        return None

    # @lru_cache(maxsize=1024)
    def get_mob_flags(self, stripped: str) -> List[str]:
        flags = [c.strip(" ").strip(".") for c in self.flag_checks if stripped.find(c) >= 0]
        return flags

    # @lru_cache(maxsize=1024)
    def get_mob_count(self, stripped: str) -> int:
        cm = self.re_mob_count.search(stripped)
        if cm is None:
            return 1

        return int(cm.groups()[0])

    # @lru_cache(maxsize=1024)
    def get_player_name(self, line: str) -> Optional[str]:
        pm = self.re_player.search(line)
        exclude = {'a', 'an', 'the', 'damaged',
                   # baramon yellow highlights
                   'hope', 'east', 'south', 'north', 'up', 'down', 'west', 'rgr', 'rock'}
        if pm is None:
            return None

        player = pm.groups()[0]
        # baramon has some mobs in the yellow color
        if player.lower() in exclude or len(player) <= 1:
            return None
        return player

    @staticmethod
    # @lru_cache(maxsize=1024)
    def has_white_color(s: str) -> bool:
        # Note this is true even in Baramon where the mobs have colorized text
        # It first sends out the code, then changes it
        return s.find('\x1b[1;37m') >= 0

    @staticmethod
    def is_blue_item(s: str) -> bool:
        return s.find('\x1b[0;36m') >= 0

    # @staticmethod
    # # @lru_cache(maxsize=1024)
    # def get_known_mob(area_name: str, mob_name):
    #
    #     if area_name not in KNOWN_AREAS:
    #         return None
    #
    #     for m in KNOWN_AREAS[area_name].known_mobs:
    #         if m.name == mob_name or m.attack_name == mob_name or m.starts_with == mob_name:
    #             return m

    # @lru_cache(maxsize=2048)
    def get_corpses(self, area_name: str, stripped: str) -> List[str]:
        flags = self.get_mob_flags(stripped)
        is_corpse = "corpse" in flags and "lying" in flags
        mob_name = self.get_mob_name(area_name, stripped)

        if not is_corpse:  # or mob_name is None:
            return []

        if mob_name:
            self.debuglog("corpse mob is %s" % mob_name)
        cm = self.re_corpse_count.search(stripped)
        if cm is None:
            count = 1
        else:
            count = int(cm.groups()[0])

        return [stripped] * count

    # @lru_cache(maxsize=2048)
    def match_encounters(self, area_name: str, line: str) -> List[encounter.Encounter]:
        has_mob_color = self.has_white_color(line[:20])
        stripped = strip_ansi_codes(line)
        mob_name = self.get_mob_name(area_name, stripped)

        # print(stripped, mob_name)
        # self.session.debug('mob_name %s' % mob_name, show=True)
        # matched name and (White or stunned or incapacitated) and not Corpse
        if mob_name is None:
            return []

        # self.session.debug("mob name %s" % mob_name, True)

        flags = self.get_mob_flags(stripped)
        is_corpse = ("corpse" in flags and "lying" in flags) or "ashes" in flags
        is_stunned = "stunned" in flags or "incapacitated" in flags
        your_follower = stripped.find("your follower") >= 0

        # self.session.show_block("enc %s %s %s %s %s" % (has_mob_color, mob_name, flags, is_corpse, is_stunned),
        #                         transmit_immediately=True)

        if (has_mob_color or is_stunned) and not is_corpse and not your_follower:
            count = self.get_mob_count(stripped)
            # known_mob = self.get_known_mob(area_name, mob_name)
            paralyzed = "paralyzed" in flags
            ranged = "ranged" in flags
            fighting = "fighting" in flags or "fighting YOU" in flags
            alert = "alert" in flags or fighting

            enc = encounter.Encounter(mob_name, ranged=ranged, paralyzed=paralyzed, flags=flags,
                                      alert=alert, fighting=fighting)
            # session.debug("encounter: %s" % mob_name, show=True )
            return [enc] * count

        return []

    def get_item_count(self, line: str) -> int:
        count = item_count_re.search(line)
        if count:
            return int(count.group(1))
        return 1
    
    def match_objects(self, line: str) -> List[item.Item]:
        is_item = item_re.match(line)
        stripped = strip_ansi_codes(line)
        blue = self.is_blue_item(line)

        if is_item:
            count = self.get_item_count(stripped)
            short = item_count_re.sub("", stripped)
            inc = item.Item(short, blue=blue, count=count)
            return [inc]

        return []

    @event("core.prompt", priority=1)
    def got_prompt(self, _: AbacuraMessage):
        """Getting a prompt ends the room"""
        # self.session.debug("room: got_prompt %s" % self.scanned_room)
        # session.debug("mobs: %s" % [m.name for m in self.scanned_room.room_mobs], show=True)
        # session.debug("corpses: %s" % self.scanned_room.room_corpses, show=True)

        if self.scanned_room is None:
            return

        # TODO: Make the latest available scanned room available somewhere
        # self.msdp.room = self.scanned_room
        self.scanned_room.msdp_exits = self.msdp.room_exits

        self.world.visited_room(area_name=self.msdp.area_name, name=self.msdp.room_name, vnum=self.msdp.room_vnum,
                                terrain=self.msdp.room_terrain, room_exits=self.msdp.room_exits,
                                scan_room=self.scanned_room)

        if self.scanned_room.vnum in self.world.rooms:
            room = self.world.rooms[self.scanned_room.vnum]
            missing_msdp_exits = any([d for d in self.msdp.room_exits if d not in room.exits])
            extra_room_exits = any([d for d in room.exits if d not in self.msdp.room_exits])
            # if missing_msdp_exits or extra_room_exits:
            #     self.session.output(Text(f"\nROOM WATCHER: Mismatch between MSDP and Room exits\n", style="purple"))

        # Load the new area if it has changed
        self.scanned_room.area = self.room.area
        if self.scanned_room.area.name != self.msdp.area_name:
            self.scanned_room.area = self.load_area(self.msdp.area_name)

        # Do not create a new instance of self.room since a reference is held by all plugins
        for f in dataclasses.fields(ScannedRoom):
            setattr(self.room, f.name, getattr(self.scanned_room, f.name))

        self.dispatch(RoomMessage(vnum=self.scanned_room.vnum, room=self.scanned_room))

        self.scanned_room = None

    # @action(r"^.* (\[ [ NSWEUD<>v^\|\(\)\[\]]* \] *$)", color=False)
    # def start_room_nocompass(self, text: OutputMessage):
    #     self.output("start no compass")
    #
    # @action(r".* \|")
    # def start_room_compass(self, text: OutputMessage):
    #     self.output("start compass")
    #
    # @action(r"^Here +- ")
    # def start_room_here(self, text: OutputMessage):
    #     self.output("Start here")
    #
    # @action(r"")

    @action(r"^There is a trail of fresh blood here leading (.*)\.")
    def blood_trail(self, direction: str):
        if self.scanned_room:
            self.scanned_room.blood_trail = direction

    @action(r"^\[\* You see your target's tracks leading (.*)\. ")
    def hunt_tracks(self, direction: str):
        if self.scanned_room:
            self.scanned_room.hunt_tracks = direction

    @action(r"\[\* You found ")
    def hunt_found(self):
        if self.scanned_room:
            self.scanned_room.hunt_tracks = "here"

        # regen_hp = scan_room and scan_room.room_header.find("RegenHp") >= 0
        # regen_mp = scan_room and scan_room.room_header.find("RegenMp") >= 0
        # regen_sp = scan_room and scan_room.room_header.find("RegenSp") >= 0
        # wild_magic = scan_room and scan_room.room_header.find('Wild Magic') >= 0
        # no_magic = scan_room and scan_room.room_header.find('NoMagic') >= 0
        # set_recall = scan_room and scan_room.room_header.find('SetRecall') >= 0
        # no_recall = scan_room and scan_room.room_header.find('Warded') >= 0
        # bank = scan_room and scan_room.room_header.find('Bank') >= 0
        # terrain = strip_ansi_codes(terrain)

    @action(r".*")
    def scan_everything(self, message: OutputMessage):
        if type(message.message) is not str:
            return
        
        # check for the start of a room name
        if self.scanned_room is None:
            if self.msdp.area_name == 'The Wilderness':
                # wilderness rooms don't have the exit list
                matched = self.match_wilderness(message.message, message.stripped)
            else:
                matched = self.match_room(message.message, message.stripped)

            if matched:
                self.scanned_room = ScannedRoom(room_header=message.stripped, vnum=self.msdp.room_vnum)

                if self.msdp.area_name == 'The Wilderness':
                    self.world.load_wilderness()

                if self.msdp.room_vnum in self.world.rooms:
                    room = self.world.rooms[self.msdp.room_vnum]

                    # copy the room attributes into the new ScanndRoom instance
                    for f in dataclasses.fields(room):
                        setattr(self.scanned_room, f.name, getattr(room, f.name))

            return

        if len(self.scanned_room.room_lines) > 100:
            return

        # otherwise, if we are in between then check for encounters/mobs & players in the room
        self.scanned_room.room_lines.append(message.message)
        encounters = self.match_encounters(self.msdp.area_name, message.message)
        objects = self.match_objects(message.message)
        corpses = self.get_corpses(self.msdp.area_name, message.stripped)
        # charmies = self.get_charmies(text.stripped)

        if len(encounters) > 0:
            self.scanned_room.room_encounters += encounters
        elif len(corpses) > 0:
            self.scanned_room.room_corpses += corpses
        elif len(objects) > 0:
            self.scanned_room.room_items += objects
        else:
            if (player_name := self.get_player_name(message.message)) is not None:
                self.scanned_room.room_players.append(player_name)

    @staticmethod
    def slugify(value):
        """
        Normalizes string, converts to lowercase, removes non-alpha characters,
        and converts spaces to hyphens.
        """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    def load_area(self, area_name: str) -> Area:
        data_dir = self.config.data_directory(self.session.name)

        new_area = Area()
        filename = os.path.join(data_dir, "areas", self.slugify(area_name) + ".toml")

        if not os.path.exists(filename):
            return new_area

        with open(filename, "r") as f:
            doc = tomlkit.load(f)

        for attribute, value in doc['area'].items():
            if hasattr(new_area, attribute):
                setattr(new_area, attribute, value)

        new_area.room_exclude = set(new_area.room_exclude)
        new_area.rooms_to_scout = set(new_area.rooms_to_scout)

        for mob_name, mob_dict in doc['mobs'].items():
            mob = Mob(name=mob_name)
            for attribute, value in mob_dict.items():
                if hasattr(mob, attribute):
                    setattr(mob, attribute, value)
            new_area.mobs.append(mob)

        self.debuglog(msg=f"Loaded area file '{filename}'")
        return new_area
