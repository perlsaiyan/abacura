import os
import re
import unicodedata
from dataclasses import fields, asdict
from itertools import takewhile
from typing import List, Pattern

from rich.console import Group
from rich.text import Text

# from atlas.known_areas import KNOWN_AREAS
from abacura.mud import OutputMessage
from abacura.plugins import command, action
from abacura.plugins.events import event, AbacuraMessage
from abacura.utils.renderables import tabulate, AbacuraPropertyGroup, AbacuraPanel
from abacura_kallisti.atlas.room import RoomHeader, RoomPlayer, RoomMob, RoomItem, RoomCorpse
from abacura_kallisti.atlas.room import ScannedMiniMap, ScannedRoom, RoomMessage
from abacura_kallisti.mud.area import Area
from abacura_kallisti.plugins import LOKPlugin


class RoomMessageParser:

    re_item_qty = re.compile("\\(([0-9]+)\\)")
    re_mob_qty = re.compile("\\[([0-9]+)\\]")

    re_normal_white = re.compile("^\\x1b\\[22;37m")
    re_item = re.compile("^\\x1b\\[0;37m.*")
    re_mob = re.compile("^(?:\\x1b\\[1;37m|\\x1b\\[0;37m\\x1b\\[1;3[0-9]m)+.*")
    re_quest = re.compile("\\x1b\\[0;37m\\.\\.\\..*may have a \\x1b\\[22;36mquest\\x1b\\[0m for you")
    re_followers = re.compile(
        r"(\w+) (?:(?:sneaks|flies|swims|crawls|stumbles|rides|arrives) (?:in)?)+(?: on(.*))? from")

    re_player = re.compile("^(?:\\x1b\\[[01](?:;[0-9]+)*m)+\\x1b\\[1;33m([A-Z]\\w+)\\x1b\\[0m")
    re_race_ride_fight = re.compile(r"^[A-Za-z]+ the (.*) is .*here(?:, riding (.*)(?:\.|and))*")

    ITEM_FLAGS = {"glows", "magic", "damaged"}

    MOB_FLAGS = {"ranged", "sneaking", "hiding", "evil", "good",
                 "grim ward", "fireshield", "acidshield", "iceshield", "shockshield", "blades",
                 "mount", "blur", "wraith", "sanc", "unholy aura", "invis", "trainer"}

    KEYWORDS = {"mortally wounded", "fighting YOU", "fighting", "resting", "incapacitated",
                "standing", "sitting", "lying", "stunned", "hovering", "your follower"}

    def __init__(self, messages: List[OutputMessage]):
        self.messages = messages
        self.has_quest: bool = False
        self.header: RoomHeader = RoomHeader('')
        self.items: List[RoomItem] = []
        self.players: List[RoomPlayer] = []
        self.mobs: List[RoomMob] = []
        self.corpses: List[RoomCorpse] = []
        self.blood_trail: str = ''
        self.hunt_tracks: str = ''

        self._parse_messages()

    @staticmethod
    def _get_quantity(stripped: str, re_qty: Pattern) -> int:
        for n in re_qty.findall(stripped):
            try:
                return int(n)
            except ValueError:
                continue

        return 1

    @staticmethod
    def _parse_junk(msg):
        if msg.stripped.startswith("You find yourself"):
            return "recall"
        elif msg.stripped.strip() == '':
            return "blank"
        elif msg.stripped.startswith('>'):
            return "junk"
        elif msg.stripped.startswith('<'):
            return "prompt"
        elif msg.stripped.startswith('WARNING!  You have entered a HARDCORE zone'):
            return "hardcore"

        return False

    def _parse_follower_arriving(self, msg):
        if m := self.re_followers.match(msg.stripped):
            player_name, mount_name = m.groups()
            p = RoomPlayer(line=msg.message, name=player_name, riding=mount_name)
            self.players.append(p)
            return p

    def _parse_player(self, msg):

        m = self.re_player.match(msg.message)
        if m:
            flags = {k for k in self.KEYWORDS if msg.stripped.find(k) >= 0}
            for text in re.findall("\\[([^\\]]+)\\]", msg.stripped):
                flags.update({f for f in self.MOB_FLAGS if text.find(f" {f} ") >= 0})

            r = self.re_race_ride_fight.match(msg.stripped)
            rg = r.groups() if r else ()
            race = rg[0] if len(rg) >= 1 else ""
            riding = rg[1] if len(rg) >= 2 else ""

            p = RoomPlayer(line=msg.message, name=m.groups()[0], flags=flags, race=race, riding=riding)
            self.players.append(p)
            return p

    def _parse_mob(self, msg: OutputMessage):

        # TODO: Test as Imm
        # starts with bold white, or starts with white followed by bold color

        if self.re_quest.match(msg.message):
            self.has_quest = True
            return "quest"

        if self.re_mob.match(msg.message):
            qty = self._get_quantity(msg.stripped, self.re_mob_qty)

            flags = set()

            m = re.match(".*\\[ ([^\\]]+) \\]", msg.stripped)
            if m:
                flag_text = m.groups()[0]
                flags = {f for f in self.MOB_FLAGS if f in flag_text}

            flags.update({k for k in self.KEYWORDS if msg.stripped.find(k) >= 0})

            fighting = "fighting" in flags or "fighting YOU" in flags
            alert = "alert" in flags or fighting

            mob = RoomMob(line=msg.message,
                          description=msg.stripped, has_quest=self.has_quest, flags=flags, quantity=qty,
                          fighting=fighting, fighting_you="fighting YOU" in flags,
                          following_you="your follower" in flags,
                          alert=alert, paralyzed="paralyzed" in flags)

            self.has_quest = False
            self.mobs.append(mob)
            return mob

    def _parse_player_mob(self, msg: OutputMessage):
        if p := self._parse_follower_arriving(msg):
            return p

        if p := self._parse_player(msg):
            return p

        return self._parse_mob(msg)

    def _parse_item(self, msg: OutputMessage):
        # TODO: Test as Imm

        if self.re_item.match(msg.message):
            qty = self._get_quantity(msg.stripped, self.re_item_qty)
            corpse = msg.stripped.find("corpse") >= 0 and msg.stripped.find("lying") >= 0
            ashes = msg.stripped.find("pile of ashes lie here") >= 0
            if corpse or ashes:
                corpse_type = "ashes" if ashes else "corpse"
                c = RoomCorpse(line=msg.message, description=msg.stripped, quantity=qty, corpse_type=corpse_type)
                self.corpses.append(c)
                return c

            item_flags = {f for f in re.findall("\\(([^\\)]+)\\)", msg.stripped) if f in self.ITEM_FLAGS}

            blue = msg.message.find('\x1b[22;36m') >= 0
            short = self.re_item_qty.sub(msg.stripped, "")
            item = RoomItem(line=msg.message, description=msg.stripped, short=short, blue=blue,
                            quantity=qty, flags=item_flags)
            self.items.append(item)
            return item

    @staticmethod
    def _parse_any(_msg):
        return "any"

    def _parse_blood(self, msg: OutputMessage):
        re_blood = re.compile(r"^There is a trail of fresh blood here leading (.*)\.")
        if m := re_blood.match(msg.stripped):
            self.blood_trail = m.groups()[0]
            return "blood"

    def _parse_tracks(self, msg: OutputMessage):
        re_tracks = re.compile(r"^\[\* You see your target's tracks leading (.*)\. ")
        re_found = re.compile(r"\[\* You found ")

        if m := re_tracks.match(msg.stripped):
            self.hunt_tracks = m.groups()[0]
            return "tracks"

        if re_found.match(msg.stripped):
            self.hunt_tracks = "here"
            return "tracks"

    def _parse_header(self) -> int:
        if len(self.messages) == 0:
            return 0

        name = time = terrain_name = weather = exits = flags = ""
        if self.messages[0].stripped.find("|") >= 0 and len(self.messages) >= 3:
            # compass
            compass = True
            re_compass0 = r"^(.*)  +([0-9]+[ap]m)* \| (.*)"
            re_compass1 = r"^(.*) +( .* )\| ([^\|]+)"
            re_compass2 = r"^(\[[^\]]+\])* +\| (.*)"

            exits0 = exits1 = exits2 = ""
            if m0 := re.match(re_compass0, self.messages[0].stripped):
                name, time, exits0 = m0.groups()
            if m1 := re.match(re_compass1, self.messages[1].stripped):
                terrain_name, weather, exits1 = m1.groups()
            if m2 := re.match(re_compass2, self.messages[2].stripped):
                flags, exits2 = m2.groups()
            exits = exits0 + exits1 + exits2

        else:
            compass = False
            re_header = r"^([^\[]+)( \[ .* \])*( \[ .* \])"
            if m0 := re.match(re_header, self.messages[0].stripped):
                name, flags, exits = m0.groups()

        weather = weather or ''
        time = time or ''
        terrain_name = terrain_name or ''
        flags = flags or ''

        if exits.lower().find("no exits") >= 0:
            exit_list = []
        else:
            exit_list = [d for d in "NSEWUD" if exits.find(d) >= 0]

        header_flags = ["RegenHp", "RegenMp", "RegenSp", "Wild Magic", "NoMagic", "SetRecall", "Warded", "Bank"]
        # "House", "Sanctum", "Vault", "Donation", "Private", "Stables", "Public", "Postern", "Shop",
        # "Entry", "Throneroom", "Altar", "Inn"

        flag_set = {f for f in header_flags if flags.find(f) >= 0}
        self.header = RoomHeader(line=self.messages[0].message, name=name.strip(), exits=exit_list,
                                 flags=flag_set, compass=compass,
                                 terrain_name=terrain_name.strip(), weather=weather.strip(), time=time.strip())
        return 3 if compass else 1

    def _parse_messages(self):
        header_lines = self._parse_header()

        parsers = [self._parse_junk, self._parse_tracks, self._parse_player_mob,
                   self._parse_item, self._parse_blood, self._parse_any]

        # process messages from bottom up
        for msg in reversed(self.messages[header_lines:]):
            # Strip leading \x1b[22;37m that happens in wilderness
            msg.message = self.re_normal_white.sub("", msg.message)

            if " tells you, '" in msg.stripped:
                continue

            for i, parser in enumerate(parsers):
                if parser(msg):
                    if parser != self._parse_any:
                        parsers = parsers[i:]
                    break

        # reverse things back to top down
        self.corpses.reverse()
        self.items.reverse()
        self.mobs.reverse()
        self.players.reverse()


class RoomWatcher(LOKPlugin):
    """Watches for LOK rooms and parses them into ScannedRoom objects"""
    def __init__(self):
        super().__init__()

        self.minimap: ScannedMiniMap = ScannedMiniMap([])
        self.last_room_messages = []
        self.re_room_no_compass = re.compile(r"^.* (\[ [ NSWEUD<>v^\|\(\)\[\]]* \] *$)")
        self.re_room_compass = re.compile(r"^.* \|")
        # self.re_room_here = re.compile(r"^Here +- ")
        self.re_room_no_exits = re.compile(r"^.* \[ No exits! \]")

        self.room_header_entry_id = -1

    @action("^(Not here!|You can't do that here)")
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

    @action(r"^\[\* You see your target's tracks leading (\w+)\.")
    def tracks(self, direction: str):
        self.room.hunt_tracks = direction

    @action(r"\[\* You found ")
    def found(self):
        self.room.hunt_tracks = "here"

    @action(r"You start searching for tracks but then realize .* is right here!")
    def found2(self):
        self.room.hunt_tracks = "here"

    @action("\x1b\\[1;35m", color=True)
    def bold_magenta(self, message: OutputMessage):
        # here_matched = self.re_room_here.match(message.stripped) is not None
        room_no_compass = self.re_room_no_compass.match(message.stripped) is not None
        room_compass = self.re_room_compass.match(message.stripped) is not None
        room_no_exits = self.re_room_no_exits.match(message.stripped) is not None
        room_wilderness = all([self.msdp.area_name == 'The Wilderness', len(message.stripped) <= 40,
                               message.message.find("\x1b[1;35m") <= 5, message.stripped.find(" - ") == -1])

        if any([room_compass, room_no_compass, room_no_exits, room_wilderness]):
            self.room_header_entry_id = self.output_history.entry_id

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
        if area_name.lower() == 'Unknown':
            return Area()

        data_dir = self.config.data_directory(self.session.name)
        filename = os.path.join(data_dir, "areas", self.slugify(area_name) + ".toml")
        new_area = Area.load_from_toml(filename)
        self.debuglog(msg=f"Loaded area file '{filename}'")
        return new_area

    def get_last_room_messages(self) -> List[OutputMessage]:
        num_lines = self.output_history.entry_id - self.room_header_entry_id + 1

        if self.room_header_entry_id < 0 or 1 > num_lines > 100:
            return []

        return [m for m in self.output_history[-num_lines:] if type(m.message) in (str, 'str')]

    def get_minimap_messages(self) -> List[OutputMessage]:
        n = self.output_history.entry_id - self.room_header_entry_id + 1

        if self.msdp.area_name == 'The Wilderness':
            minimap_lines = takewhile(lambda m: m.stripped.startswith(" "), self.output_history[-n + 1:])
            return list(minimap_lines)

        # traverse lines above room header in reverse order
        past_50_lines = [m for m in self.output_history[-n - 1:-n - 50:-1] if type(m.message) in (str, 'str')]

        # if compass is on, first line above room header will be blank, skip it
        if len(past_50_lines) > 0 and past_50_lines[0].stripped.strip(" ") == '':
            past_50_lines = past_50_lines[1:]

        def looks_like_minimap(m):
            return m.stripped.strip() != "" and m.stripped.startswith(" ")

        minimap_lines = list(takewhile(looks_like_minimap, past_50_lines))
        minimap_lines.reverse()

        return minimap_lines

    @event("core.prompt", priority=1)
    def got_prompt(self, _: AbacuraMessage):
        if self.room_header_entry_id >= 0:
            try:
                self.last_room_messages = self.get_last_room_messages()
                rmp = RoomMessageParser(self.last_room_messages)
                minimap = ScannedMiniMap(self.get_minimap_messages())
            except Exception as e:
                self.debuglog(str(e))
                return

            self.room_header_entry_id = -1

            sr = ScannedRoom(vnum=self.msdp.room_vnum, name=self.msdp.room_name, minimap=minimap,
                             terrain_name=self.msdp.room_terrain, msdp_exits=self.msdp.room_exits,
                             blood_trail=rmp.blood_trail, hunt_tracks=rmp.hunt_tracks,
                             header=rmp.header, items=rmp.items, mobs=rmp.mobs,
                             corpses=rmp.corpses, players=rmp.players)

            if self.msdp.area_name == 'The Wilderness':
                self.world.load_wilderness()

            # Copy the saved room attributes into the new ScanndRoom instance
            if self.msdp.room_vnum in self.world.rooms:
                room = self.world.rooms[self.msdp.room_vnum]
                for f in fields(room):
                    setattr(sr, f.name, getattr(room, f.name))

            # Override these since they show up in the header
            sr.bank = "bank" in sr.header.flags
            sr.set_recall = "SetRecall" in sr.header.flags
            sr.wild_magic = "Wild Magic" in sr.header.flags
            sr.regen_hp = "RegenHp" in sr.header.flags
            sr.regen_mp = "RegenMp" in sr.header.flags
            sr.regen_sp = "RegenSp" in sr.header.flags
            sr.warded = "Warded" in sr.header.flags
            sr.no_magic = "NoMagic" in sr.header.flags

            self.world.visited_room(area_name=self.msdp.area_name, name=self.msdp.room_name, vnum=self.msdp.room_vnum,
                                    terrain=self.msdp.room_terrain, room_exits=self.msdp.room_exits,
                                    scan_room=sr)

            if sr.vnum in self.world.rooms:
                room = self.world.rooms[self.msdp.room_vnum]
                missing_msdp_exits = any([d for d in self.msdp.room_exits if d not in room.exits])
                extra_room_exits = any([d for d in room.exits if d not in self.msdp.room_exits])
                if missing_msdp_exits or extra_room_exits:
                    self.debuglog(f"\nRoomWatcher: Mismatch between MSDP & Room exits")

            # Load the new area if it has changed
            sr.area = self.room.area
            if self.msdp.area_name not in [sr.area.name] + sr.area.include_areas:
                sr.area = self.load_area(self.msdp.area_name)

            sr.identify_room_mobs()

            # TODO: Change lokplugin.room to a property so we can replace the object
            # Do not create a new instance of self.room since a reference is held by all plugins
            for f in fields(ScannedRoom):
                setattr(self.room, f.name, getattr(sr, f.name))

            self.dispatch(RoomMessage(vnum=sr.vnum, room=sr))

    def save_room_messages(self):
        from pathlib import Path
        import pickle

        data_dir = Path(self.config.data_directory(self.session.name)).expanduser()
        data_dir.mkdir(exist_ok=True)

        file = data_dir / f"{self.msdp.room_vnum}.pkl"
        with open(file, "wb") as f:
            pickle.dump(self.last_room_messages, f)
        self.output(f"Dumped [ {self.msdp.room_vnum} ] messages into {file}", highlight=True)

    def test_room_messages(self, vnum: str):
        from pathlib import Path
        import pickle
        data_dir = Path(self.config.data_directory(self.session.name)).expanduser()
        file = data_dir / f"{vnum}.pkl"

        if not file.exists():
            self.output(f"{file} does not exist")
            return

        with open(file, "rb") as f:
            messages = pickle.load(f)

        for msg in messages:
            self.output(Text.from_ansi(msg.message))

        rmp = RoomMessageParser(messages)
        self.output(rmp.header)
        self.output(rmp.corpses)
        self.output(rmp.items)
        self.output(rmp.players)
        if rmp.blood_trail:
            self.output(f"blood={rmp.blood_trail}")
        if rmp.hunt_tracks:
            self.output(f"tracks={rmp.hunt_tracks}")

    @command(name="scanroom", hide=True)
    def scanroom_command(self, save: bool = False, _load: str = ""):
        """
        Display details about most recently scanned room, optionally save debugging info

        :param save: Save the most recently scanned room into a <vnum>.pkl file in data directory
        :param _load: Load a saved .pkl file and display results of processing it
        """

        if save:
            self.save_room_messages()
            return

        if _load:
            self.test_room_messages(_load)
            return

        properties = {'vnum': self.room.vnum, 'area': self.room.area.name}
        properties.update(asdict(self.room.header))
        properties['blood'] = self.room.blood_trail
        properties['hunt'] = self.room.hunt_tracks

        rows = []
        for corpse in self.room.corpses:
            rows.append(("corpse", f"{corpse.description}", corpse.quantity, "", corpse.corpse_type, ''))

        for item in self.room.items:
            rows.append(("item", f"{item.description}", item.quantity,
                         f"{'blue item' if item.blue else ''}", item.flags, ''))

        for mob in self.room.mobs:
            details = {}
            if mob.level > 0:
                details = {"level": mob.level, "race": mob.race}

            rows.append(("mob", f"{mob.description}", mob.quantity,
                         f"{'has_quest' if mob.has_quest else ''}", mob.flags, details))

        for player in self.room.players:
            rows.append(("player", f"{player.name:}", '', player.race, player.flags, ''))

        property_view = AbacuraPropertyGroup(properties, "Properties", exclude={"line"})
        table = tabulate(rows, headers=["Type", "Description", "Qty", "Misc", "Flags", "Details"],
                         title="Contents", caption=f"count: {len(rows)}")
        group = Group(property_view, Text(""), table)
        panel = AbacuraPanel(group, title=f"Scanned Room [ {self.room.vnum} ]")
        self.output(panel, highlight=True)
