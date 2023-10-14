#!/usr/bin/env python

# script to import tt map data to sqlite

"""
Tables:
CREATE TABLE exits(from_vnum,direction,to_vnum,door,closes,locks,key_name,weight,max_level,min_level,deathtrap, commands, PRIMARY KEY (from_vnum, direction))
CREATE TABLE rooms(vnum,name,terrain_name,area_name,regen_hp,regen_mp,regen_sp,set_recall,peaceful,deathtrap,silent,wild_magic,bank,narrow,no_magic,no_recall, last_visited, last_harvested, primary key (vnum))

int fields:
closes, locks, weight, max_lev, min_lev, deahtrap (0/1)
string fields:
from_vnum, to_vnum, direction, key_name, commands

Need to:
parse map file for rooms with room info
exits with exit info
don't need room_tracking

"""
# note: room 24736 has a command west to transfer to aartuat, but it doesn't match the msdp exit vnum
# can only go that way if level 50 or higher
"""
Sample rooms:

R = room
E = exit

e/r	vnum	dir	color		room_name		?		?		area		?	terrain	?		wt			?
R {  208} {0} {<178>} {The Arena} { } {} {Arena} {} {Field} {} {1.000} {}

ex	vnum	dir	cmd	BV		?	?		weight	?	?
E {  209} {e} {e} {2} {0} {} {1.000} {} {0.00}
E {  205} {n} {n} {1} {0} {} {1.000} {} {0.00}
E {  207} {w} {w} {8} {0} {} {1.000} {} {0.00}

"""


import re
import sqlite3

import click


def strip_ansi(text):
    ''''''
    # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    result = ansi_escape.sub('', text)
    return result


class RoomRecord:
    insert_statement = "INSERT OR IGNORE INTO rooms(vnum,name,terrain_name,area_name,regen_hp,regen_mp,regen_sp,set_recall,peaceful,deathtrap,silent,wild_magic,bank,narrow,no_magic,no_recall, last_visited,last_harvested) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

    def __init__(self):
        ''''''
        # vnum,name,terrain_name,area_name,regen_hp,regen_mp,regen_sp,set_recall,peaceful,deathtrap,silent,wild_magic,bank,narrow,no_magic,no_recall, last_visited, last_harvested
        self.vnum = int()
        self.name = ''
        self.terrain_name = ''
        self.area_name = ''
        self.regen_hp = 0
        self.regen_mp = 0
        self.regen_sp = 0
        self.set_recall = 0
        self.peaceful = 0
        self.deathrap = 0
        self.silent = 0
        self.wild_magic = 0
        self.bank = 0
        self.narrow = 0
        self.no_magic = 0
        self.no_recall = 0
        self.last_visited = None
        self.last_harvested = None


class ExitRecord:
    insert_statement = "INSERT OR IGNORE INTO exits(from_vnum,direction,to_vnum,door,closes,locks,key_name,weight,max_level,min_level,deathtrap, commands) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"

    full_dirs = {
        'e': 'east',
        'w': 'west',
        's': 'south',
        'n': 'north',
        'u': 'up',
        'd': 'down',
    }

    fixed_commands = ['turn', 'enter', 'push', 'pull', 'visit', 'say']

    def __init__(self):
        ''''''
        # from_vnum,direction,to_vnum,door,closes,locks,key_name,weight,max_level,min_level,deathtrap, commands
        self.from_vnum = int()
        self.direction = ''
        self.to_vnum = int()
        self.door = ''
        self.closes = 0
        self.locks = 0
        self.key_name = ''
        self.weight = 0
        self.max_level = 100
        self.min_level = 0
        self.deathtrap = 0
        self.commands = ''

    def translate_exit(self, _exit):
        ''''''
        if _exit in ExitRecord.full_dirs.keys():
            return ExitRecord.full_dirs[_exit]
        else:
            return _exit

    def clean_commands(self, _command):
        ''''''
        if _command in ExitRecord.full_dirs.keys():
            return None
        else:
            return _command

    def parse_command(self, _command):
        ''''''
        command = _command
        if command == '1.5':
            return 'say yes'
        cmd = _command.split(';')
        if len(cmd) > 1:
            if cmd[0].startswith('gg'):
                cmd.pop(0)
            if cmd[0].startswith('unl'):
                cmd.pop(0)
            for _cmd in cmd:
                if _cmd.startswith('gt'):
                    return None
        if len(cmd) > 1:
            command = ";".join(cmd)
        else:
            command = cmd[0]
        return command

    def parse_dirs(self, _dir):
        ''''''
        dir = _dir
        if _dir.startswith('secret'):
            dir = re.sub("secret", "", _dir)
        for i in ExitRecord.fixed_commands:
            if _dir.startswith(i):
                dirs = _dir.split()
                dir = dirs[1]
        return dir


"""
			for _cmd in ExitRecord.fixed_commands:
				if _cmd in cmd[0]:
					cmd_parts = _cmd.split()
					dir = cmd_parts[1]
"""


@click.command()
@click.help_option('--help', '-h')
@click.option(
    '--infile',
    '-i',
    help='Input file for tintin map data (default "map_data.txt")',
    default='map_data.txt',
)
@click.option(
    '--outfile',
    '-o',
    help='Output file for abacura map database (default "worldtest.db")',
    default='worldtest.db',
)
def main(infile, outfile):
    ''''''
    con = sqlite3.connect(outfile)
    cur = con.cursor()

    cur.execute("DROP TABLE exits;")
    cur.execute("DROP TABLE rooms;")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS exits(from_vnum,direction,to_vnum,door,closes,locks,key_name,weight,max_level,min_level,deathtrap, commands, PRIMARY KEY (from_vnum, direction))"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS rooms(vnum,name,terrain_name,area_name,regen_hp,regen_mp,regen_sp,set_recall,peaceful,deathtrap,silent,wild_magic,bank,narrow,no_magic,no_recall, last_visited, last_harvested, primary key (vnum))"
    )

    # pattern for rooms gives:
    # vnum, 0, room name, ' ', zone, terrain, weight

    # pattern for exits gives:
    # to_vnum, direction, commands, BV, '0', 'weight', '0.00'

    pattern = "{([a-zA-Z 0-9\\.;,\-\/'&]+)}"
    count = {'total': 0, 'rooms': 0, 'exits': 0, 'bad_rooms': 0, 'bad_exits': 0}

    with open(infile) as fh:
        last_rnum = None
        for line in fh:
            if line:
                line = strip_ansi(line)
                line = re.sub("(;\d\dm)", "", line)
                vals = re.findall(pattern, line)
                vals = list(map(lambda v: v.strip(), vals))
                record_vals = []
                if line.startswith('R'):
                    last_rnum = vals[0]
                    r = RoomRecord()
                    # vnum,name,terrain_name,area_name,regen_hp,regen_mp,regen_sp,set_recall,peaceful,deathtrap,silent,wild_magic,bank,narrow,no_magic,no_recall, last_visited, last_harvested
                    r.vnum = vals[0]
                    # We stop if we get a vnum over 61000, currently excluding wilderness, and abacura's automapper will map anywhere with vnums we encounter there
                    if int(r.vnum) > 61000:
                        print("Vnum over 61k:", r.vnum)
                        con.commit()
                        con.close()
                        # close file handler too
                        print(
                            f"Total of {count['rooms']} rooms and {count['exits']} exits processed."
                        )
                        print(f"Total number of bad rooms: {count['bad_rooms']}")
                        print(f"Total number of bad exits: {count['bad_exits']}")
                        print(f"Total number of records processed: {count['total']}")
                        print(
                            f"Does {count['rooms'] + count['exits']} == {count['total']}?"
                        )
                        exit()
                    r.name = vals[2]
                    if len(r.name) == 0:
                        last_rnum = None
                        count['bad_rooms'] += 1
                        continue
                    r.area_name = vals[4]
                    r.terrain_name = vals[5]
                    count['rooms'] += 1
                    count['total'] += 1
                elif line.startswith('E'):
                    # E {46099} {s} {open gate s;s} {4} {0} {} {1.000} {} {0.00}
                    # to_vnum, direction, commands, BV, '0', 'weight', '0.00'
                    # from_vnum,direction,to_vnum,door,closes,locks,key_name,weight,max_level,min_level,deathtrap, commands
                    if last_rnum is None:
                        # debug print('Bad room data, not writing exit')
                        count['bad_exits'] += 1
                        continue
                    r = ExitRecord()
                    r.from_vnum = last_rnum
                    r.to_vnum = vals[0]
                    r.direction = r.translate_exit(vals[1])
                    if r.direction not in r.full_dirs:
                        r.direction = r.parse_dirs(r.direction)
                    r.commands = r.clean_commands(vals[2])
                    if r.commands == r.direction:
                        r.commands = None
                    if r.commands is not None:
                        if 'open' in r.commands:
                            # there's a door here
                            r.closes = 1
                        if 'unl' in r.commands and r.closes == 1:
                            # the door locks
                            r.locks = 1
                        r.commands = r.parse_command(r.commands)
                    if r.commands == 'say yes' and r.direction == 'north':
                        continue
                    count['exits'] += 1
                    count['total'] += 1
                if last_rnum is not None:
                    for k, v in vars(r).items():
                        record_vals.append(v)
                    insert_vals = tuple(record_vals)
                    # print(f"{r.insert_statement}, {insert_vals}")
                    cur.execute(r.insert_statement, insert_vals)


if __name__ == '__main__':
    main()


"""
These are commands that have unlock, we know these doors close/lock
+---------------------------------------------------------------------+
|                              commands                               |
+---------------------------------------------------------------------+
| unlock gate;open gate;east                                          |
| gg midgaard;unlock gate s;open gate s;s                             |
| gg manager;unlock door south;open door south;south;close door north |
+---------------------------------------------------------------------+
in this case, we want r.closes and r.locks to be set to 1

other commands such as open gate north;north give us door name/direction and closes
we want to parse commands and:
assign door name if not door,
assign closes,
assign locks if command contains unlock

These are unique directions:
| enter portal    |
| secretdown      |
| secretup        |
| turn pedestal   |
| enter pylon     |
| sphinx          |
| enter root      |
| say autumn      |
| say spring      |
| say summer      |
| say winter      |
| enter pattern   |
| enter tent      |
| home            |
| visit clan      |
| turn sundial    |
| turn spike      |
| say yes         |
| enter tree      |
| enter rock      |
| enter wagon     |
| enter pool      |
| enter black     |
| enter mirror    |
| enter stones    |
| depart          |
| enter pipe      |
| enter drainpipe |
| enter tunnel    |
| enter airshaft  |
+-----------------+

we want to port this into commands, and anything that's enter/turn/say, the direction should be the second word, such as tent, clan, sundial.
depart/home should port to command and remain
for example:
enter tree should become: direction: tree, command: enter
"""
