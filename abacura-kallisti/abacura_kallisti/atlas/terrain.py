from dataclasses import dataclass
from typing import Dict
from functools import lru_cache


@dataclass(slots=True)
class Terrain:
    name: str
    symbol: str
    symbol_sort: int
    color: str
    color_sort: int
    weight: int
    impassable: bool = False
    stamina: int = 0
    bg_color: str = 'black'


SKILL_TERRAIN = {'gather': ['Field', 'Hills'],
                 'mine': ['Mountains'],
                 'fish': ['Water'],
                 'log': ['Forest'],  # , 'Jungle'],
                 # for searching every room in wilderness
                 'search': ['Field', 'Hills', 'Mountains', 'Forest', 'Jungle', 'Swamp',
                            'Lush Forest', 'Beach', 'Desert', 'Arctic', 'Snow', 'Underground']
                 # 'search': ['Field', 'Hills', 'Forest']
                 }


_TERRAIN_LIST = [
    # Special terrain
    Terrain(name='', symbol=' ', symbol_sort=1, color='black', color_sort=1, weight=10, bg_color='black'),
    Terrain(name=' ', symbol=' ', symbol_sort=1, color='black', color_sort=1,  weight=10, bg_color='black'),
    Terrain(name='You', symbol='@', symbol_sort=1, color='bright_red', color_sort=1, weight=0, bg_color='black'),
    Terrain(name='Unknown', symbol='?', symbol_sort=1, color='red', color_sort=1, weight=4, bg_color='black'),
    Terrain(name='?', symbol='?', symbol_sort=1, color='black', color_sort=1, weight=4),

    Terrain(name='Air', symbol=".", symbol_sort=8, color="white", color_sort=5, weight=1),
    Terrain(name='Arctic', symbol="_", symbol_sort=8, color="bright_white", color_sort=3, weight=7, bg_color='white'),
    Terrain(name='Astral', symbol='.', symbol_sort=9, color='white', color_sort=5, weight=3),
    Terrain(name='Beach', symbol='~', symbol_sort=4, color='bright_yellow', color_sort=3, weight=4, bg_color='cyan'),
    Terrain(name="Bridge", symbol="=", symbol_sort=1, color="bright_yellow", color_sort=2, weight=1),
    Terrain(name="City", symbol="+", symbol_sort=10, color="white", color_sort=3, weight=2),
    Terrain(name='Deep', symbol='~', symbol_sort=1, color='blue', color_sort=3, weight=6, bg_color='cyan'),
    Terrain(name='Desert', symbol='.', symbol_sort=1, color='bright_yellow', color_sort=9, weight=4, bg_color='yellow'),
    Terrain(name="Fence", symbol='|', symbol_sort=5, color='green', color_sort=3, weight=3),
    Terrain(name="Field", symbol='.', symbol_sort=7, color='bright_green', color_sort=4, weight=3, bg_color='green'),
    Terrain(name="Forest", symbol='*', symbol_sort=5, color='green', color_sort=3, weight=3, bg_color='green'),
    Terrain(name='ForestJungle', symbol='x', symbol_sort=3, color='bright_green', color_sort=7, weight=4),
    Terrain(name='Hills', symbol=')', symbol_sort=6, color='yellow', color_sort=3, weight=5, bg_color='yellow'),
    Terrain(name='Inside', symbol='o', symbol_sort=7, color='bright_white', color_sort=5, weight=1),
    Terrain(name='Jungle', symbol='x', symbol_sort=4, color='bright_green', color_sort=6, weight=7, bg_color='green'),
    Terrain(name='Lava', symbol='~', symbol_sort=1, color='bright_red', color_sort=9, weight=99, impassable=True, bg_color='red'),
    Terrain(name='Lush', symbol='x', symbol_sort=1, color='bright_green', color_sort=9, weight=3),
    Terrain(name='Mountains', symbol='^', symbol_sort=7, color='white', color_sort=3, weight=9, bg_color='yellow'),
    Terrain(name='Ocean', symbol='~', symbol_sort=1, color='bright_blue', color_sort=9, weight=99, impassable=True, bg_color='blue'),
    Terrain(name='Pasture', symbol='.', symbol_sort=4, color='green', color_sort=6, weight=3),
    Terrain(name="Path", symbol="-", symbol_sort=2, color="yellow", color_sort=10, weight=1),
    Terrain(name='Peak', symbol='^', symbol_sort=1, color='bright_white', color_sort=1, weight=99, impassable=True, bg_color='yellow'),
    Terrain(name='Planar', symbol='.', symbol_sort=9, color='white', color_sort=3, weight=1),
    Terrain(name='Portal', symbol='&', symbol_sort=2, color='white', color_sort=8, weight=1),
    Terrain(name='Shallow', symbol='~', symbol_sort=2, color='bright_cyan', color_sort=8, weight=6),
    Terrain(name='Snow', symbol='_', symbol_sort=1, color='bright_white', color_sort=9, weight=5, bg_color='white'),
    Terrain(name='Stairs', symbol='v', symbol_sort=0, color='white', color_sort=5, weight=4),
    Terrain(name='Swamp', symbol='~', symbol_sort=4, color='black', color_sort=6, weight=8, bg_color='green'),
    Terrain(name='Tundra', symbol='.', symbol_sort=4, color='bright_white', color_sort=4, weight=5, bg_color='white'),
    Terrain(name='Underground', symbol='o', symbol_sort=11, color='bright_white', color_sort=3, weight=3, bg_color='black'),
    Terrain(name='Underwater', symbol='~', symbol_sort=1, color='blue', color_sort=9, weight=7),
    Terrain(name="Water", symbol='~', symbol_sort=3, color='bright_cyan', color_sort=3, weight=6, bg_color='cyan'),
]

# Create a lookup
_TERRAIN: Dict[str, Terrain] = {t.name: t for t in _TERRAIN_LIST}


@lru_cache(maxsize=500)
def get_terrain(terrain_name: str) -> Terrain:
    names = [name for name in terrain_name.split(" ") if name in _TERRAIN]
    if not len(names):
        return Terrain(name=terrain_name, symbol='?', symbol_sort=1, color='white', color_sort=1, weight=4)

    symbol = sorted([(_TERRAIN[name].symbol_sort, _TERRAIN[name].symbol) for name in names])[0][1]
    color = sorted([(_TERRAIN[name].color_sort, _TERRAIN[name].color) for name in names])[0][1]
    bg_color = sorted([(_TERRAIN[name].color_sort, _TERRAIN[name].bg_color) for name in names])[0][1]
    impassable = any([_TERRAIN[name].impassable for name in names])
    weight = max([_TERRAIN[name].weight for name in names])
    return Terrain(name=terrain_name, symbol=symbol, symbol_sort=1, color=color, color_sort=1,
                   impassable=impassable, weight=weight, bg_color=bg_color)
