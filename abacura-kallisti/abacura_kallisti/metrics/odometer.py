from abacura_kallisti.metrics import MudMetrics
from abacura_kallisti.mud.msdp import TypedMSDP
from typing import List
from datetime import datetime


class Odometer:
    def __init__(self, msdp: TypedMSDP):
        self.metrics: MudMetrics = MudMetrics()
        self.metric_history: List[MudMetrics] = []
        self.msdp = msdp

        # DONE TODO: start_time should be none initially
        # DONE TODO: add metrics to history upon starting them

    def start(self, mission: str):
        self.stop()

        # DONE TODO: Set Start time here, don't default it
        self.metrics = MudMetrics(mission=mission, character_name=self.msdp.character_name,
                                  start_time=datetime.now(),
                                  start_xp=self.msdp.experience, start_gold=self.msdp.gold,
                                  start_bank=self.msdp.bank_gold)

        self.metric_history.append(self.metrics)

    def stop(self):
        # DONE TODO: If there is no start time then there is nothing to stop
        if self.metrics.start_time is None:
            return

        if self.metrics.stop_time is None:
            self.metrics.stop_time = datetime.now()

    def reset_history(self):
        # DONE TODO: create brand new metrics when resetting, don't put them into history
        self.metrics = MudMetrics()
        self.metric_history = []

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
