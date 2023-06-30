from collections import Counter
from datetime import datetime
from functools import lru_cache
from typing import List, Dict

from .terrain import get_terrain, SKILL_TERRAIN
from .wilderness import WildernessGrid
from .world import World


TINTIN_COLORS = {
    'black': 'aaa',
    'red': 'daa',
    'green': 'ada',
    'yellow': 'dda',
    'blue': 'aad',
    'magenta': 'dad',
    'cyan': 'add',
    'white': 'ddd',
    'gray': 'ddd',
    'bright_red': 'faa',
    'bright_green': 'afa',
    'bright_yellow': 'ffa',
    'bright_blue': 'aaf',
    'bright_magenta': 'ffa',
    'bright_cyan': 'aff',
    'bright_white': 'fff'
}


class WildernessMap:
    """
    Used to create smaller, "down-sampled" maps of wilderness.
    Special care is taken with "landmark" terrain including water, peaks, lava, etc
    """
    def __init__(self, world: World):
        """
        :param world: The world with the list of all known rooms
        """
        self.grid = WildernessGrid()
        self.world = world
        self.sampled_you: bool = False
        self.sampled_gummton: bool = False

    def sample(self, center_point, radii,
               skill: str = '', since: datetime = None, you_vnum: str = '') -> (str, bool):
        """
        Sample the terrain around a specific point in wilderness.
        Reduces that terrain to a single terrain value
        Optionally determine if that area has been harvested recently
        :param center_point: The sample point
        :param radii: How much terrain to sample around that point
        :param skill: Highlight a particular harvesting skill (gathering, logging, etc.)
        :param since: Determine if the terrain has been harvested since this date (typically uptime)
        :param you_vnum: Put an @ in this room
        :return:
        """
        counts = Counter()
        cx, cy = center_point
        xr, yr = radii
        harvestable_count: int = 0
        harvestable_terrain = SKILL_TERRAIN.get(skill, [])
        for ys in range(int(cy - yr), int(cy + yr) + 1):
            if not 0 <= ys < self.grid.HEIGHT:
                continue

            for xs in range(int(cx - xr), int(cx + xr) + 1):
                if not 0 <= xs < self.grid.WIDTH:
                    continue

                sample_vnum = self.grid.get_vnum(self.grid.UPPER_LEFT, xs, ys)
                room = self.world.rooms.get(sample_vnum, None)
                if room is not None:
                    if room.vnum == you_vnum and not self.sampled_you:
                        counts['You'] += 1
                    else:
                        counts[room.terrain] += 1

                    recently_harvested = False
                    tr = self.world.get_tracking(room.vnum)
                    skill_date = tr.last_harvested if skill != 'search' else tr.last_searched
                    if since is not None and skill_date is not None and skill_date != '':
                        recently_harvested = skill_date >= since

                    if room.terrain in harvestable_terrain and not recently_harvested:
                        harvestable_count += 1

        # start with the most common terrain
        mc = counts.most_common()
        # print(mc)
        try:
            sample_terrain = mc[0][0]
        except IndexError:
            sample_terrain = ''

        sampled_area = max(1, sum(counts.values()))
        harvestable = harvestable_count >= 0.4 * sampled_area

        # Override based on percent of area for specific terrain types to highlight certain features
        # Override percentages change with scale of map
        terrain_pct = [('You', 0), ('Underground', 0),  # any of these and we override
                       ('Lava', 100/sampled_area), ('Arctic', 200/sampled_area), ('Snow', 600/sampled_area),
                       ('Water', max(12.0, sampled_area/10)), ('Peak', 400/sampled_area), ('Mountains', 35)]

        if not self.sampled_gummton and 'Field Bridge' in counts:
            self.sampled_gummton = True
            sample_terrain = 'Field Bridge'
        elif not self.sampled_you and 'You' in counts:
            self.sampled_you = True
            sample_terrain = 'You'
        else:
            for t, pct in terrain_pct:
                if counts[t] > sampled_area * pct / 100:
                    sample_terrain = t
                    break

        return sample_terrain, harvestable

    @staticmethod
    def get_bg_color_code(bright: int, bg_color: str) -> str:
        bg_color = bg_color.replace('bright_', '')

        # return '<B%s>' % TINTIN_COLORS[bg_color]
        return '<%s>' % TINTIN_COLORS[bg_color].upper()

    @staticmethod
    def get_fg_color_code(fg_color: str) -> str:
        return '<%s>' % TINTIN_COLORS[fg_color]

    def get_map(self, width: int, height: int, you_vnum: str, symbol_overrides: Dict[str, str]) -> List[str]:
        map_lines: List[str] = []

        if you_vnum not in ['?', ''] and int(you_vnum) < 70000:
            return map_lines

        y_radius: int = (height - 1) // 2
        x_radius: int = (width - 1) // 2

        for delta_y in range(-y_radius, y_radius + 1):
            map_line = ""
            last_fg: str = ''
            last_bg: str = ''

            for delta_x in range(-x_radius, x_radius + 1):
                vnum = self.grid.get_vnum(you_vnum, delta_x, delta_y)
                # print('%d, %d: %s' % (delta_x, delta_y, vnum))
                terrain: str = ' '
                if vnum == you_vnum:
                    terrain = 'You'
                elif vnum in self.world.rooms:
                    terrain = self.world.rooms[vnum].terrain

                fg, bg = self.get_terrain_color_codes(terrain)

                if fg != last_fg:
                    map_line += fg
                    last_fg = fg

                if bg != last_bg:
                    map_line += bg
                    last_bg = bg

                symbol = symbol_overrides.get(vnum, get_terrain(terrain).symbol)
                # print('map: [%s] %d,%d %s' % (vnum, delta_x, delta_y, symbol))
                # row.append(symbol_overrides.get(vnum, TERRAIN[terrain].symbol))
                map_line += symbol

            map_lines.append(map_line)

        return map_lines

    def get_scaled_map(self, scale_width: int = 100, scale_height: int = 30, ruler: bool = False, you_vnum: str = '',
                       skill: str = '', since: datetime = None) -> List[str]:
        scaled_map = []
        map_lines: List[str] = []
        self.sampled_you = False
        self.sampled_gummton = False

        x_scale = self.grid.WIDTH / (scale_width - 1)
        y_scale = self.grid.HEIGHT / (scale_height - 1)
        x_radius = x_scale / 2
        y_radius = y_scale / 2
        radii = (x_radius, y_radius)
        area = (2*x_radius+1)*(2*y_radius+1)
        print("scaled map: ", (scale_width, scale_height), (x_scale, y_scale), radii, area)

        for y in range(scale_height):
            row = []
            for x in range(scale_width):
                cx = round(x * x_scale)
                cy = round(y * y_scale)
                center = (cx, cy)
                row.append(self.sample(center, radii, skill, since, you_vnum))
            scaled_map.append(row)

        if ruler:
            x_ruler = [u"\u001b[0;37m\u001b[48;5;0m  "] + ["%d" % (x % 10) for x in range(len(scaled_map[0]))]
            x_ruler = "".join(x_ruler)
            map_lines = [x_ruler]

        for y in range(len(scaled_map)):
            s = ''
            if ruler:
                s = u"\u001b[38;5;7m\u001b[48;5;0m" + "%d " % (y % 10)

            for x in range(len(scaled_map[0])):
                terrain_name, harvestable = scaled_map[y][x]

                # if terrain_name not in TERRAIN:
                #     terrain_name = '?'

                bg_color_override = ''
                if skill != '' and harvestable and terrain_name in SKILL_TERRAIN[skill]:
                    bg_color_override = 'magenta'

                fg, bg = self.get_terrain_color_codes(terrain_name, bg_color_override)
                s += fg + bg + get_terrain(terrain_name).symbol

            map_lines.append(s)

        return map_lines

    @lru_cache(100)
    def get_terrain_color_codes(self, terrain_name: str, bg_color_override: str = '') -> (str, str):

        terrain = get_terrain(terrain_name)
        fg_color = terrain.color
        bg_color = fg_color if terrain.bg_color == '' else terrain.bg_color

        if bg_color_override:
            bg_color = bg_color_override

        bright = 1 if fg_color.startswith('bright') else 0

        bg_color_code = self.get_bg_color_code(bright, bg_color)
        fg_color_code = self.get_fg_color_code(fg_color)

        return bg_color_code, fg_color_code
