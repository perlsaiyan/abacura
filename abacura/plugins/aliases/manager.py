from __future__ import annotations

import csv
import io
import re
from typing import Dict, TYPE_CHECKING
from rich.panel import Panel
from rich.pretty import Pretty
from abacura.plugins import Plugin, command

if TYPE_CHECKING:
    from abacura import Session
    from abacura.config import Config

class AliasManager(Plugin):
    """Alias manager"""

    session: Session
    config: Config
    def __init__(self):
        super().__init__()
        self.aliases: Dict[str, str] = {}
        self.aliases["test"] = r'kill %1;loot %1;smile %2'
        self.re_param = re.compile(r'^%([0-9]+)')

    def handle(self, cmd, line):
        """Handle aliases, return True if success, False if missing"""
        if cmd in self.aliases:
            args = line.split()
            try:
                command_list = csv.reader(io.StringIO(self.aliases[cmd]), delimiter=';', escapechar='\\')
                lines = command_list.__next__()
                for alias_line in lines:

                    file_like = io.StringIO(alias_line)
                    parts = next(csv.reader(file_like, delimiter=' '))
                    #self.session.output(f"[bold yellow] PREPARSE: {list(parts)}", markup = True)
                    parsed = []
                    for token in parts:
                        m = self.re_param.match(token)
                        if m:
                            parsed.append(args[int(m.group(1))] if int(m.group(1)) < len(args) else r'')
                        else:
                            parsed.append(token)
                    #self.session.output(f"Parsed: {parsed}")
                    parsed_alias = ' '.join(parsed)

                    # SEND
                    #self.session.output(f"[bold yellow] SEND: {parsed_alias}", markup = True)
                    self.session.player_input(parsed_alias)

            except StopIteration:
                pass

            return True
        return False
    
    @command(name="alias")
    def alias(self):
        """list, remove add aliases"""
        buf = "[bold white]Aliases:\n"
        for key in self.aliases.items():
            self.session.output(Pretty(key), actionable=False)
            buf += f"{key[0]}: {key[1]}\n"
        
        self.session.output(Panel(buf), actionable=False)