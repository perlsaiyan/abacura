from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class Terrain:
    name: str
    symbol: str
    color: str
    weight: int
    impassable: bool = False
    # bg_color is used for the wilderness map
    bg_color: str = ''


COLORS = {'black':   0,
          'red':     1,
          'green':   2,
          'yellow':  3,
          'blue':    4,
          'magenta': 5,
          'cyan':    6,
          'white':   7,
          'bright_black': 8,
          'gray': 8,
          'grey': 8,
          'bright_red': 9,
          'bright_green': 10,
          'bright_yellow': 11,
          'bright_blue': 12,
          'bright_magenta': 13,
          'bright_cyan': 14,
          'bright_white': 15
          }


SKILL_TERRAIN = {'gather': ['Field', 'Hills'],
                 'mine': ['Mountains'],
                 'fish': ['Shallow Water', 'Deep Water', 'Water'],
                 'log': ['Forest'],  # , 'Jungle'],
                 # for searching every room in wilderness
                 'search': ['Field', 'Hills', 'Mountains', 'Forest', 'Jungle', 'Swamp',
                            'Lush Forest', 'Beach', 'Desert', 'Arctic', 'Snow', 'Underground']
                 # 'search': ['Field', 'Hills', 'Forest']
                 }


TERRAIN_LIST = [
    # Special terrain
    Terrain(name='', symbol=' ', color='black', weight=10, bg_color='black'),
    Terrain(name=' ', symbol=' ', color='black', weight=10, bg_color='black'),
    Terrain(name='You', symbol='@', color='bright_red', weight=0, bg_color='black'),
    Terrain(name='Unknown', symbol='?', color='red', weight=4, bg_color='black'),
    Terrain(name='?', symbol='?', color='black', weight=4),

    # impassable terrain
    Terrain(name='Lava', symbol='~', color='bright_red', weight=100, impassable=True, bg_color='red'),
    Terrain(name='Peak', symbol='^', color='bright_white', weight=100, impassable=True, bg_color='yellow'),
    Terrain(name='Ocean', symbol='~', color='bright_blue', weight=100, impassable=True, bg_color='blue'),

    # Astral/Planar, need better symbols
    Terrain(name='Astral', symbol='.', color='white', weight=3),
    Terrain(name='Bridge Astral', symbol='=', color='white', weight=3),
    Terrain(name='Forest Planar', symbol='*', color='white', weight=4),
    Terrain(name='Inside Planar', symbol='o', color='white', weight=3),
    Terrain(name='Inside Astral', symbol='o', color='white', weight=4),
    Terrain(name='Field Astral', symbol='.', color='white', weight=4),
    Terrain(name='Planar', symbol='.', color='white', weight=3),

    # Regular terrain
    Terrain(name='Air', symbol='.', color='white', weight=4),
    Terrain(name='Arctic', symbol='_', color='bright_white', weight=4, bg_color='white'),
    Terrain(name='Beach', symbol='~', color='bright_yellow', weight=4, bg_color='cyan'),
    Terrain(name='Bridge', symbol='=', color='yellow', weight=1),
    Terrain(name='Bridge Path', symbol='=', color='yellow', weight=1),
    Terrain(name='City', symbol='+', color='white', weight=1),
    Terrain(name='City Beach', symbol='~', color='bright_yellow', weight=3),
    Terrain(name='City Bridge', symbol='=', color='bright_yellow', weight=1),
    Terrain(name='City Bridge Path', symbol='=', color='bright_yellow', weight=1),
    Terrain(name='City Bridge Path Stairs', symbol='=', color='bright_yellow', weight=1),
    Terrain(name='City Field', symbol='.', color='bright_green', weight=3),
    Terrain(name='City Field Path', symbol='-', color='white', weight=1),
    Terrain(name='City Forest', symbol='*', color='bright_green', weight=3),
    Terrain(name='City Hills', symbol=')', color='green', weight=3),
    Terrain(name='City Path', symbol='-', color='white', weight=1),
    Terrain(name='City Portal', symbol='&', color='white', weight=2),
    Terrain(name='City Underground', symbol='+', color='white', weight=2),
    Terrain(name='City Water', symbol='~', color='bright_cyan', weight=4),
    Terrain(name='Deep Water', symbol='~', color='blue', weight=8, bg_color='cyan'),
    Terrain(name='Desert', symbol='.', color='bright_yellow', weight=4, bg_color='yellow'),
    Terrain(name='Field', symbol='.', color='bright_green', weight=4, bg_color='green'),
    Terrain(name='Field Arctic', symbol='.', color='bright_white', weight=6),
    Terrain(name='Field Beach', symbol='~', color='bright_yellow', weight=2, bg_color='cyan'),
    Terrain(name='Field Bridge', symbol='=', color='bright_yellow', weight=2, bg_color='green'),
    Terrain(name='Field Forest', symbol='.', color='green', weight=4),
    Terrain(name='Field Forest Path', symbol='-', color='green', weight=4),
    Terrain(name='Field Hills', symbol=')', color='green', weight=3),
    Terrain(name='Field Path', symbol='-', color='green', weight=1),
    Terrain(name='Field Swamp Path', symbol='-', color='green', weight=4),
    Terrain(name='Lush Forest', symbol='x', color='bright_green', weight=4, bg_color='green'),
    Terrain(name='Forest', symbol='*', color='bright_green', weight=4, bg_color='green'),
    Terrain(name='Forest Mountains', symbol='^', color='green', weight=6),
    Terrain(name='Forest Path', symbol='-', color='green', weight=1),
    Terrain(name='Forest Hills', symbol='*', color='bright_green', weight=4),
    Terrain(name='Forest Water', symbol='~', color='bright_cyan', weight=8),
    Terrain(name='Forest Swamp', symbol='*', color='green', weight=8),
    Terrain(name='Forest Swamp Path', symbol='*', color='green', weight=4),
    Terrain(name='Hills', symbol=')', color='bright_green', weight=6, bg_color='yellow'),
    Terrain(name='Hills Arctic', symbol=')', color='bright_white', weight=6),
    Terrain(name='Hills Path', symbol='-', color='yellow', weight=1),
    Terrain(name='Inside', symbol='o', color='bright_white', weight=2),
    Terrain(name='Inside Arctic', symbol='-', color='bright_white', weight=3),
    Terrain(name='Inside Bridge', symbol='=', color='bright_white', weight=1),
    Terrain(name='Inside City', symbol='o', color='bright_white', weight=1),
    Terrain(name='Inside City Path', symbol='-', color='white', weight=1),
    Terrain(name="Inside City Stairs", symbol='v', color='white', weight=1),
    Terrain(name="Inside City Underground", symbol="o", color="white", weight=2),
    Terrain(name="Inside City Underground Path", symbol="-", color="white", weight=1),
    Terrain(name='Inside Forest', symbol='*', color='green', weight=3),
    Terrain(name='Inside Mountains', symbol='^', color='white', weight=6),
    Terrain(name='Inside Mountains Underground', symbol='^', color='white', weight=6),
    Terrain(name='Inside Underground', symbol='o', color='white', weight=3),
    Terrain(name='Inside Water Underground', symbol='~', color='cyan', weight=7),
    Terrain(name='Jungle', symbol='X', color='bright_green', weight=20, bg_color='green'),
    Terrain(name='Jungle ForestJungle', symbol='x', color='bright_green', weight=20, bg_color='green'),
    Terrain(name='Jungle Path ForestJungle', symbol='-', color='bright_green', weight=20, bg_color='green'),
    Terrain(name='Jungle Swamp ForestJungle', symbol='x', color='bright_green', weight=20, bg_color='black'),
    Terrain(name='Mountains', symbol='^', color='black', weight=8, bg_color='yellow'),
    Terrain(name='Mountains Arctic', symbol='^', color='bright_white', weight=8),
    Terrain(name='Mountains Arctic Path', symbol='-', color='white', weight=2),
    Terrain(name='Mountains Path', symbol='-', color='yellow', weight=2),
    Terrain(name='Pasture', symbol='.', color='green', weight=3),
    Terrain(name='Path', symbol='-', color='yellow', weight=1),
    Terrain(name='Portal', symbol='&', color='white', weight=2),
    Terrain(name='Snow', symbol='_', color='bright_white', weight=4, bg_color='white'),
    Terrain(name='Swamp', symbol='~', color='black', weight=16, bg_color='green'),
    Terrain(name='Swamp Path', symbol='-', color='white', weight=4),
    Terrain(name='Underground', symbol='o', color='bright_white', weight=2, bg_color='black'),
    Terrain(name='Underground Bridge', symbol='=', color='white', weight=4),
    Terrain(name='Underwater', symbol='~', color='blue', weight=10),
    Terrain(name='Underground Swamp', symbol='~', color='green', weight=12),
    Terrain(name='Water', symbol='~', color='bright_cyan', weight=5, bg_color='cyan'),
    Terrain(name='Water Arctic', symbol='~', color='bright_white', weight=5),
    Terrain(name='Water Swamp', symbol='~', color='green', weight=8),
    Terrain(name='Water Underground', symbol='~', color='bright_cyan', weight=4)
]

# Create a lookup
TERRAIN: Dict[str, Terrain] = {t.name: t for t in TERRAIN_LIST}
