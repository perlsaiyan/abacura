from dataclasses import dataclass
from enum import Enum
import re

from abacura_kallisti.plugins import LOKPlugin
from abacura.plugins import command


item_re = re.compile(r'(\x1b\[0m)?\x1b\[0;37m[^\x1b ]')

class TelluriaSection(Enum):
    c = 1
    ne = 2
    nw = 3
    sw = 4

@dataclass
class TelluriaGrid:
    section: TelluriaSection
    x: int
    y: int


telluria_decoder = {
    '* .. ':  TelluriaGrid(TelluriaSection.ne, 0, 0),
    '. *~*':  TelluriaGrid(TelluriaSection.ne, 1, 0),
    '~ ~..':  TelluriaGrid(TelluriaSection.ne, 2, 0),
    '. **~':  TelluriaGrid(TelluriaSection.ne, 3, 0),
    '* . .':  TelluriaGrid(TelluriaSection.ne, 4, 0),
    '.*~* ':  TelluriaGrid(TelluriaSection.ne, 0, 1),
    '*.~~.':  TelluriaGrid(TelluriaSection.ne, 1, 1),
    '~~***':  TelluriaGrid(TelluriaSection.ne, 2, 1),
    '*.~.~':  TelluriaGrid(TelluriaSection.ne, 3, 1),
    '.*~ *':  TelluriaGrid(TelluriaSection.ne, 4, 1),
    '~..~ ':  TelluriaGrid(TelluriaSection.ne, 0, 2),
    '~***~':  TelluriaGrid(TelluriaSection.ne, 1, 2),
    '*~~~~':  TelluriaGrid(TelluriaSection.ne, 2, 2),
    '~**~*':  TelluriaGrid(TelluriaSection.ne, 3, 2),
    '~.. ~':  TelluriaGrid(TelluriaSection.ne, 4, 2),
    '.~** ':  TelluriaGrid(TelluriaSection.ne, 0, 3),
    '*~.~.':  TelluriaGrid(TelluriaSection.ne, 1, 3),
    '~*~**':  TelluriaGrid(TelluriaSection.ne, 2, 3),
    '*~..~':  TelluriaGrid(TelluriaSection.ne, 3, 3),
    '.~* *':  TelluriaGrid(TelluriaSection.ne, 4, 3),
    '*. .o':  TelluriaGrid(TelluriaSection.ne, 0, 4),
    '.* ~*':  TelluriaGrid(TelluriaSection.ne, 1, 4),
    '~~ ..':  TelluriaGrid(TelluriaSection.ne, 2, 4),
    '.* *~':  TelluriaGrid(TelluriaSection.ne, 3, 4),
    '*.  .':  TelluriaGrid(TelluriaSection.ne, 4, 4),
    '. ~~ ':  TelluriaGrid(TelluriaSection.nw, 0, 0),
    '~ .*.':  TelluriaGrid(TelluriaSection.nw, 1, 0),
    '* *~~':  TelluriaGrid(TelluriaSection.nw, 2, 0),
    '~ ..*':  TelluriaGrid(TelluriaSection.nw, 3, 0),
    '. ~ ~':  TelluriaGrid(TelluriaSection.nw, 4, 0),
    '~.*. ':  TelluriaGrid(TelluriaSection.nw, 0, 1),
    '.~**~':  TelluriaGrid(TelluriaSection.nw, 1, 1),
    '**...':  TelluriaGrid(TelluriaSection.nw, 2, 1),
    '.~*~*':  TelluriaGrid(TelluriaSection.nw, 3, 1),
    '~.* .':  TelluriaGrid(TelluriaSection.nw, 4, 1),
    '*~~* ':  TelluriaGrid(TelluriaSection.nw, 0, 2),
    '*...*':  TelluriaGrid(TelluriaSection.nw, 1, 2),
    '.****':  TelluriaGrid(TelluriaSection.nw, 2, 2),
    '*..*.':  TelluriaGrid(TelluriaSection.nw, 3, 2),
    '*~~ *':  TelluriaGrid(TelluriaSection.nw, 4, 2),
    '~*.. ':  TelluriaGrid(TelluriaSection.nw, 0, 3),
    '.*~*~':  TelluriaGrid(TelluriaSection.nw, 1, 3),
    '*.*..':  TelluriaGrid(TelluriaSection.nw, 2, 3),
    '.*~~*':  TelluriaGrid(TelluriaSection.nw, 3, 3),
    '~*. .':  TelluriaGrid(TelluriaSection.nw, 4, 3),
    '.~ ~ ':  TelluriaGrid(TelluriaSection.nw, 0, 4),
    '~. *.':  TelluriaGrid(TelluriaSection.nw, 1, 4),
    '** ~~':  TelluriaGrid(TelluriaSection.nw, 2, 4),
    '~. .*':  TelluriaGrid(TelluriaSection.nw, 3, 4),
    '.~o ~':  TelluriaGrid(TelluriaSection.nw, 4, 4),
    '~ ** ':  TelluriaGrid(TelluriaSection.sw, 0, 0),
    '* ~.~':  TelluriaGrid(TelluriaSection.sw, 1, 0),
    '. .**':  TelluriaGrid(TelluriaSection.sw, 2, 0),
    '* ~~.':  TelluriaGrid(TelluriaSection.sw, 3, 0),
    '~ *o*':  TelluriaGrid(TelluriaSection.sw, 4, 0),
    '*~.~ ':  TelluriaGrid(TelluriaSection.sw, 0, 1),
    '~*..*':  TelluriaGrid(TelluriaSection.sw, 1, 1),
    '..~~~':  TelluriaGrid(TelluriaSection.sw, 2, 1),
    '~*.*.':  TelluriaGrid(TelluriaSection.sw, 3, 1),
    '*~. ~':  TelluriaGrid(TelluriaSection.sw, 4, 1),
    '.**. ':  TelluriaGrid(TelluriaSection.sw, 0, 2),
    '.~~~.':  TelluriaGrid(TelluriaSection.sw, 1, 2),
    '~....':  TelluriaGrid(TelluriaSection.sw, 2, 2),
    '.~~.~':  TelluriaGrid(TelluriaSection.sw, 3, 2),
    '.** .':  TelluriaGrid(TelluriaSection.sw, 4, 2),
    '*.~~ ':  TelluriaGrid(TelluriaSection.sw, 0, 3),
    '~.*.*':  TelluriaGrid(TelluriaSection.sw, 1, 3),
    '.~.~~':  TelluriaGrid(TelluriaSection.sw, 2, 3),
    '~.**.':  TelluriaGrid(TelluriaSection.sw, 3, 3),
    '*.~ ~':  TelluriaGrid(TelluriaSection.sw, 4, 3),
    '~* * ':  TelluriaGrid(TelluriaSection.sw, 0, 4),
    '*~ .~':  TelluriaGrid(TelluriaSection.sw, 1, 4),
    '.. **':  TelluriaGrid(TelluriaSection.sw, 2, 4),
    '*~ ~.':  TelluriaGrid(TelluriaSection.sw, 3, 4),
    '~*  *':  TelluriaGrid(TelluriaSection.sw, 4, 4),
    'o. *~':  TelluriaGrid(TelluriaSection.c, 0, 0)
}


class Telluria(LOKPlugin):
    """Determine room in telluria based on minimap"""

    @command
    def telluria(self):
        """
        Show current location in telluria (requires that minimap is enabled)
        """
        terrain_symbols = {'Forest': '*', 'Desert': '.', 'Tundra': '~', 'Inside': 'o'}
        t = terrain_symbols.get(self.msdp.room_terrain, ' ')
        t += self.room.minimap.grid.get((0, -1), ' ')
        t += self.room.minimap.grid.get((0, +1), ' ')
        t += self.room.minimap.grid.get((+1, 0), ' ')
        t += self.room.minimap.grid.get((-1, 0), ' ')

        telluria_location = telluria_decoder.get(t, None)
        self.output(f"Telluria Location: {telluria_location} : '{t}'")
