import re
from functools import lru_cache
from typing import List


SURVEY_TERRAIN = {'. 0 32': 'Field',
                  '. 1 32': 'Field',
                  '. 0 33': 'Desert',
                  '. 1 33': 'Desert',
                  '* 0 32': 'Forest',
                  '- 0 33': 'Path',
                  ') 0 32': 'Hills',
                  '^ 0 33': 'Mountains',
                  '^ 1 37': 'Peak',
                  '. 1 37': 'Air',
                  '+ 1 30': 'City',
                  '= 1 33': 'Bridge',
                  '@ 1 31': 'You',
                  '~ 1 36': 'Water',
                  '~ 1 31': 'Lava',
                  '~ 0 36': 'Deep Water',
                  '~ 0 34': 'Underwater',
                  '~ 1 34': 'Ocean',
                  '~ 0 33': 'Beach',
                  'x 1 32': 'Jungle',
                  '_ 1 37': 'Arctic',
                  '- 0 32': 'Swamp',
                  '= 0 33': 'Bridge',
                  'o 0 37': 'Inside'
                  }

SURVEY_MATERIALS = {'f': 'fish',
                    'h': 'herbs',
                    'o': 'ore',
                    'T': 'wood',
                    'm': 'magic',
                    'c': 'cloth'
                    }

SURVEY_SYMBOLS = {'M': 'mob',
                  'P': 'player',
                  'X': 'cabin',
                  '?': 'unknown',
                  '@': 'you'
                  }

# ^[[0;32m. ^[[0;37mField         ^[[1;36m~ ^[[0;37mShallow Water
# ^[[0;33m. ^[[0;37mDesert        ^[[0;36m~ ^[[0;37mDeep Water
# ^[[0;32m* ^[[0;37mForest        ^[[0;34m~ ^[[0;37mUnderwater
# ^[[0;33m- ^[[0;37mTrail         ^[[0;33m~ ^[[0;37mBeach
# ^[[0;32m( ^[[0;37mHills         ^[[1;32mx ^[[0;37mJungle
# ^[[0;33m^ ^[[0;37mMountain      ^[[1;37m_ ^[[0;37mSnow
# ^[[1;37m^ ^[[0;37mPeak          ^[[0;32m- ^[[0;37mSwamp
# ^[[0;37m. ^[[0;37mAir           ^[[0;33m= ^[[0;37mBridge
# ^[[1;30m+ ^[[0;37mCity          ^[[0;37mo ^[[0;37mInside


# strip leading spaces
# split it into commands and non-commands
# command is escape through m
class WildernessRoom:
    def __init__(self, symbol: str, color: int, bright: bool):
        self.symbol: str = symbol
        self.color: int = color
        self.bright: bool = bright
        self.delta_x: int = 0
        self.delta_y: int = 0
        self.vnum: str = ''
        self.material: str = SURVEY_MATERIALS.get(symbol, '')

    def __str__(self):
        return '{%2d,%2d %5s: %1s %5.5s}' % (self.delta_x, self.delta_y, self.vnum, self.symbol, self.get_terrain())

    def __repr__(self):
        return self.__str__()

    def get_terrain(self) -> str:
        # figure out the terrain based on what we saw in the survey
        if self.symbol == ' ':
            return 'empty'

        lookup = '%s %d %d' % (self.symbol, self.bright, self.color)
        return SURVEY_TERRAIN.get(lookup, 'unknown')

    def get_name(self) -> str:
        name_map = {'Mountains': 'Mountain', 'Water': 'Shallow Water', 'Path': 'Trail'}
        t = self.get_terrain()
        return name_map.get(t, t)


class WildernessGrid:
    WIDTH = 351
    HEIGHT = 166
    UPPER_LEFT = 69999
    split_re = re.compile(r'(\x1b\[[^m]+m)')
    color_re = re.compile(r'\x1b\[(\d);(\d+)m')

    def parse_minimap(self, lines, you_vnum: str = '') -> List[List[WildernessRoom]]:
        cur_color: int = 32
        cur_bright: bool = False
        rows: List[List[WildernessRoom]] = []
        you_row: int = 0
        you_col: int = 0
        if you_vnum == '' or you_vnum == '?' or int(you_vnum) < self.UPPER_LEFT:
            return rows

        for line in lines:
            # if not line.startswith(' '):
            #     continue

            row = []
            line = line.strip('\n')
            matches = self.split_re.split(line)
            for match in matches:
                c = self.color_re.match(match)
                if c is not None:
                    cur_bright = c.groups()[0] == '1'
                    cur_color = int(c.groups()[1])
                else:
                    for x in match:
                        cell = WildernessRoom(x, cur_color, cur_bright)
                        if cell.get_terrain() == 'You':
                            you_row = len(rows)
                            you_col = len(row)
                        row.append(cell)

            rows.append(row)

        for y, row in enumerate(rows):
            for x, cell in enumerate(row):
                cell.delta_y = y - you_row
                cell.delta_x = x - you_col
                if you_vnum is not None and cell.get_terrain() != 'empty':
                    cell.vnum = self.get_vnum(you_vnum, cell.delta_x, cell.delta_y)

        return rows

    # assert(get_vnum('87523', -1, 0)=='')
    # assert(get_vnum('87523', -2, 0)=='87522')
    # assert(get_vnum('87523', 0, -1)=='87173')
    @lru_cache(100)
    def get_vnum(self, vnum: str, delta_x: int, delta_y: int) -> str:
        if delta_x == 0 and delta_y == 0:
            return vnum

        x, y = self.get_point(vnum)
        new_x = x + delta_x
        new_y = y + delta_y

        if new_x < 0 or new_x >= self.WIDTH:
            return ''

        if new_y < 0 or new_y >= self.HEIGHT:
            return ''

        return self.get_vnum_at_point(new_x, new_y)

    def get_vnum_at_point(self, x: int, y: int) -> str:
        # there is a hole at this location, which corresponds with vnum 87523
        if y == 49 and x == 325:
            return ''

        vnum = self.UPPER_LEFT + self.WIDTH * y + x

        # everything is shifted due to the hole
        if vnum >= 87523:
            vnum -= 1

        return str(vnum)

    def get_point(self, vnum: str):
        v = int(vnum)

        # everything is shifted due to the hole
        if v >= 87523:
            v += 1

        d = v - self.UPPER_LEFT
        y = d // self.WIDTH
        x = d % self.WIDTH
        return x, y

    def get_orienteering_point(self, vnum: str):
        x, y = self.get_point(vnum)

        ox = x + 1
        oy = 165 - y
        return ox, oy

    def get_distance(self, from_vnum: str, to_vnum: str) -> int:
        from_x, from_y = self.get_point(from_vnum)
        to_x, to_y = self.get_point(to_vnum)

        # use "manhattan" distance since we can only move n, s, e, w
        distance = abs(from_x - to_x) + abs(from_y - to_y)
        return distance

    def get_exits(self, vnum: str) -> {}:
        remove_exits = {'87172': 'south', '87522': 'east',
                        '87523': 'west', '87873': 'north'}

        v = int(vnum)
        x, y = self.get_point(vnum)
        dirs = []

        if x > 0:
            dirs.append(('west', -1))
        if x < self.WIDTH:
            dirs.append(('east', 1))
        if y > 0:
            dirs.append(('north', -self.WIDTH))
        if y < self.HEIGHT:
            dirs.append(('south', self.WIDTH))

        exits = {d: str(v + delta) for d, delta in dirs if v + delta >= self.UPPER_LEFT}

        if vnum in remove_exits:
            exits = {k: v for k, v in exits.items() if k not in remove_exits[vnum]}

        return exits
