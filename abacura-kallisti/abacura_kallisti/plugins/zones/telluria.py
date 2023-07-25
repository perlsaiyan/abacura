import re

# from atlas.known_areas import KNOWN_AREAS
from abacura.plugins import command
from abacura_kallisti.plugins import LOKPlugin

item_re = re.compile(r'(\x1b\[0m)?\x1b\[0;37m[^\x1b ]')


telluria_decoder = {
    '* .. ':  ('ne', 0, 0),
    '. *~*':  ('ne', 1, 0),
    '~ ~..':  ('ne', 2, 0),
    '. **~':  ('ne', 3, 0),
    '* . .':  ('ne', 4, 0),
    '.*~* ':  ('ne', 0, 1),
    '*.~~.':  ('ne', 1, 1),
    '~~***':  ('ne', 2, 1),
    '*.~.~':  ('ne', 3, 1),
    '.*~ *':  ('ne', 4, 1),
    '~..~ ':  ('ne', 0, 2),
    '~***~':  ('ne', 1, 2),
    '*~~~~':  ('ne', 2, 2),
    '~**~*':  ('ne', 3, 2),
    '~.. ~':  ('ne', 4, 2),
    '.~** ':  ('ne', 0, 3),
    '*~.~.':  ('ne', 1, 3),
    '~*~**':  ('ne', 2, 3),
    '*~..~':  ('ne', 3, 3),
    '.~* *':  ('ne', 4, 3),
    '*. .o':  ('ne', 0, 4),
    '.* ~*':  ('ne', 1, 4),
    '~~ ..':  ('ne', 2, 4),
    '.* *~':  ('ne', 3, 4),
    '*.  .':  ('ne', 4, 4),
    '. ~~ ':  ('nw', 0, 0),
    '~ .*.':  ('nw', 1, 0),
    '* *~~':  ('nw', 2, 0),
    '~ ..*':  ('nw', 3, 0),
    '. ~ ~':  ('nw', 4, 0),
    '~.*. ':  ('nw', 0, 1),
    '.~**~':  ('nw', 1, 1),
    '**...':  ('nw', 2, 1),
    '.~*~*':  ('nw', 3, 1),
    '~.* .':  ('nw', 4, 1),
    '*~~* ':  ('nw', 0, 2),
    '*...*':  ('nw', 1, 2),
    '.****':  ('nw', 2, 2),
    '*..*.':  ('nw', 3, 2),
    '*~~ *':  ('nw', 4, 2),
    '~*.. ':  ('nw', 0, 3),
    '.*~*~':  ('nw', 1, 3),
    '*.*..':  ('nw', 2, 3),
    '.*~~*':  ('nw', 3, 3),
    '~*. .':  ('nw', 4, 3),
    '.~ ~ ':  ('nw', 0, 4),
    '~. *.':  ('nw', 1, 4),
    '** ~~':  ('nw', 2, 4),
    '~. .*':  ('nw', 3, 4),
    '.~o ~':  ('nw', 4, 4),
    '~ ** ':  ('sw', 0, 0),
    '* ~.~':  ('sw', 1, 0),
    '. .**':  ('sw', 2, 0),
    '* ~~.':  ('sw', 3, 0),
    '~ *o*':  ('sw', 4, 0),
    '*~.~ ':  ('sw', 0, 1),
    '~*..*':  ('sw', 1, 1),
    '..~~~':  ('sw', 2, 1),
    '~*.*.':  ('sw', 3, 1),
    '*~. ~':  ('sw', 4, 1),
    '.**. ':  ('sw', 0, 2),
    '.~~~.':  ('sw', 1, 2),
    '~....':  ('sw', 2, 2),
    '.~~.~':  ('sw', 3, 2),
    '.** .':  ('sw', 4, 2),
    '*.~~ ':  ('sw', 0, 3),
    '~.*.*':  ('sw', 1, 3),
    '.~.~~':  ('sw', 2, 3),
    '~.**.':  ('sw', 3, 3),
    '*.~ ~':  ('sw', 4, 3),
    '~* * ':  ('sw', 0, 4),
    '*~ .~':  ('sw', 1, 4),
    '.. **':  ('sw', 2, 4),
    '*~ ~.':  ('sw', 3, 4),
    '~*  *':  ('sw', 4, 4),
    'o. *~':  ('c', 0, 0)
}


class Tellurida(LOKPlugin):

    @command
    def telluria(self):
        terrain_symbols = {'Forest': '*', 'Desert': '.', 'Tundra': '~', 'Inside': 'o'}
        t = terrain_symbols.get(self.msdp.room_terrain, ' ')
        t += self.room2.minimap.grid.get((0, -1), ' ')
        t += self.room2.minimap.grid.get((0, +1), ' ')
        t += self.room2.minimap.grid.get((+1, 0), ' ')
        t += self.room2.minimap.grid.get((-1, 0), ' ')

        telluria_location = telluria_decoder.get(t, None)
        self.output(f"Telluria Location: {telluria_location} : '{t}'")
