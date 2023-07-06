from __future__ import annotations

import csv
from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import tomlkit
from typing import Dict, List, Optional, TYPE_CHECKING

from serum import inject

from abacura.plugins.events import event


if TYPE_CHECKING:
    from abacura.mud.options.msdp import MSDPMessage
    from abacura import Session
    from abacura.config import Config

@dataclass
class Alias:
    category: str
    cmd: str
    value: str
    temporary: bool = False

@inject
class AliasManager:
    """Alias manager"""

    session: Session
    config: Config

    def __init__(self):
        super().__init__()
        self.aliases: List[Alias] = []
        self.re_param = re.compile(r'^%([0-9]+)')

    @staticmethod
    def parse_alias(alias) -> (str, str):
        s = alias.split(".")
        name = s[1] if len(s) > 1 else s[0]
        category = s[0] if len(s) > 1 else None

        return name, category

    def get_alias(self, alias: str) -> Optional[Alias]:
        cmd, category = self.parse_alias(alias)
        for a in self.aliases:
            if a.cmd == cmd and (a.category == category or category is None):
                return a

        return None    

    def get_categories(self) -> List[str]:
        unique_categories = {a.category for a in self.aliases}
        return list(sorted(unique_categories))        

    def get_category(self, category: str) -> List[Alias]:
        return [ali for ali in self.aliases if ali.category.lower() == category.lower()]
    
    def get_alias_by_command(self, cmd: str) -> Alias:
        for a in self.aliases:
            if a.cmd == cmd:
                return a
        return None

    def delete_alias(self, alias: str):
        existing_alias = self.get_alias(alias)
        self.aliases = [ali for ali in self.aliases if ali != existing_alias]
        self.save()

    def add_alias(self, alias: str, value: str, temporary: bool = False):
        name, category = self.parse_alias(alias)

        if self.get_alias(alias) is None:
            self.aliases.append(Alias(category, name, value, temporary))
            self.save()

    def save(self):
        toml_structure = {}
        for c in self.get_categories():
            toml_structure[c] = {ali.cmd: ali.value for ali in self.get_category(c) if not ali.temporary}

        with open(self.alias_filepath, 'w') as f:
            tomlkit.dump(toml_structure, f)        

    def load(self, file: str):
        self.alias_filepath = Path(os.path.join(self.session.config.data_directory(self.session.name), f"{file}"))
        if not self.alias_filepath.exists():
            self.alias_filepath.parent.mkdir(parents=True, exist_ok=True)
            self.alias_filepath.touch()

        if os.path.isfile(self.alias_filepath):
            self.session.debuglog(msg=f"Import aliases from '{self.alias_filepath}'")
            with open(self.alias_filepath, 'r') as f:
                toml_structure = tomlkit.load(f)
            aliases: List[Alias] = []
            for c in toml_structure.keys():
                aliases += [Alias(c, k, v) for k, v in toml_structure[c].items()]

            self.aliases = aliases

    def handle(self, cmd, line):
        """Handle aliases, return True if success, False if missing"""
        alias = self.get_alias_by_command(cmd)
        if alias:
            args = line.split()
            try:
                command_list = csv.reader(io.StringIO(alias.value), delimiter=';', escapechar='\\')
                lines = command_list.__next__()
                for alias_line in lines:

                    file_like = io.StringIO(alias_line)
                    parts = next(csv.reader(file_like, delimiter=' '))
                    # self.session.output(f"[bold yellow] PREPARSE: {list(parts)}", markup = True)
                    parsed = []
                    for token in parts:
                        m = self.re_param.match(token)
                        if m:
                            parsed.append(args[int(m.group(1))] if int(m.group(1)) < len(args) else r'')
                        else:
                            parsed.append(token)
                    # self.session.output(f"Parsed: {parsed}")
                    parsed_alias = ' '.join(parsed)

                    # SEND
                    # self.session.output(f"[bold yellow] SEND: {parsed_alias}", markup = True)
                    self.session.player_input(parsed_alias)

            except StopIteration:
                pass

            return True
        return False
