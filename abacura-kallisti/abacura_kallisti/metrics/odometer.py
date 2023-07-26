from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from abacura.plugins.events import AbacuraMessage
from abacura_kallisti.metrics import MudMetrics
from abacura_kallisti.mud.msdp import TypedMSDP


@dataclass
class OdometerMessage(AbacuraMessage):
    event_type: str = "lok.odometer"
    value: str = ""
    odometer: List[MudMetrics] = field(default_factory=list)


class Odometer:
    def __init__(self, msdp: TypedMSDP):
        self.metrics: MudMetrics = MudMetrics()
        self.metric_history: List[MudMetrics] = []
        self.msdp = msdp

    def start(self, mission: str):
        if self.metrics.stop_time is None:
            self.metrics.end_exp = self.msdp.experience
            self.metrics.end_gold = self.msdp.gold
            self.metrics.end_bank = self.msdp.bank_gold
            self.metrics.stop_time = datetime.now()

        self.metrics = MudMetrics(mission=mission, character_name=self.msdp.character_name,
                                  start_time=datetime.now(),
                                  start_xp=self.msdp.experience, end_xp=self.msdp.experience,
                                  start_gold=self.msdp.gold, end_gold=self.msdp.gold,
                                  start_bank=self.msdp.bank_gold, end_bank=self.msdp.bank_gold)

        self.metric_history.append(self.metrics)

    def clear_history(self):
        self.metrics = MudMetrics()
        self.metric_history.clear()
        self.start(mission=self.msdp.area_name)

    @staticmethod
    def get_quality_number(quality: str):
        qualities = {'junk': 1, 'rough': 2, 'average': 4, 'good': 6, 'excellent': 7,
                     'superior': 8, 'pristine': 9, 'exquisite': 10, 'flawless': 11,
                     'divine': 12, 'divine quality': 12}
        return qualities.get(quality, 0)

    @staticmethod
    def get_quality_value(quality: str) -> int:
        qualities = {'junk': 0, 'rough': 0, 'average': 4500, 'good': 10800, 'excellent': 17150,
                     'superior': 25600, 'pristine': 36450, 'exquisite': 50000, 'flawless': 66550,
                     'divine': 86400, 'divine quality': 86400}
        return qualities.get(quality, 0) * .75
