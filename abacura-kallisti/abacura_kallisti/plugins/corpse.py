from dataclasses import dataclass

from abacura.plugins import action
from abacura.plugins.events import AbacuraMessage
from abacura_kallisti.plugins import LOKPlugin


@dataclass
class CorpseMessage(AbacuraMessage):
    """Message when a room is viewed"""
    size: str = ""
    weight: int = 0
    value: int = 0
    corpse_type: str = ''
    race: str = ''
    level: int = 0
    event_type: str = "lok.corpse"


class CorpseScanner(LOKPlugin):
    def __init__(self):
        super().__init__()
        self.last_size = ''
        self.last_weight = 0
        self.last_value = 0

    @action(r"^Weight: (\d+) stones, Value: (\d+) coins, Size: (.*)")
    def corpse_weight(self, weight: int, value: int, size: str):
        self.last_weight = weight
        self.last_value = value
        self.last_size = size

    @action(r"^Corpse type: (.*), Race of deceased: (.*), Level: (\d+)")
    def corpse(self, corpse_type: str, race: str, level: int):
        self.dispatcher(CorpseMessage(race=race, level=level, size=self.last_size,
                                      weight=self.last_weight, value=self.last_value, corpse_type=corpse_type))
