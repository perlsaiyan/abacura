"""
Player structure

Includes current player information, and preferences
"""
from dataclasses import dataclass, field
import os
from tomlkit import parse, TOMLDocument, document

from abacura import Config

@dataclass(slots=True)
class PlayerCharacter:
    """Kallisti specific player information"""
    _config: TOMLDocument = field(default_factory=document)
    home_vnum: str = ''
    egress_vnum: str = '3001'
    recall_vnum: str = '3001'
    char_name: str = ''

    def load(self, data_dir: str, name: str):
        self.char_name = name.lower()

        char_file = os.path.join(data_dir, self.char_name)
        char_file = f"{char_file}.player"
        if not os.path.isfile(char_file):
            with open(char_file, 'w', encoding="UTF-8") as fp:
                fp.write(f"char_name = '{self.char_name}'\n")

        self._config = parse(open(char_file, "r", encoding="UTF-8").read())
        for key, val in self._config.items():
            if hasattr(self,key):
                setattr(self, key, val)
