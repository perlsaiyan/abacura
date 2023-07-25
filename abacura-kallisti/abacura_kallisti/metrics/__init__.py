from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from collections import Counter


@dataclass
class EarnedXP:
    source: str = ""
    victim: str = ""
    xp: int = 0


@dataclass
class EarnedGold:
    source: str = ""
    victim: str = ""
    gold: int = 0


@dataclass
class MudMetrics:
    mission: str = ""
    character_name: str = ""
    area_name: str = ""
    
    start_time: Optional[datetime] = None  # field(default_factory=datetime.now)
    stop_time: Optional[datetime] = None

    earned_xp: List[EarnedXP] = field(default_factory=list)
    earned_gold: List[EarnedGold] = field(default_factory=list)

    counters: Counter = field(default_factory=Counter)
    info: Dict = field(default_factory=dict)

    start_xp: int = 0
    start_gold: int = 0
    start_bank: int = 0

    end_xp: int = 0
    end_gold: int = 0
    end_bank: int = 0

    kills: int = 0

    craft_qualities: Counter = field(default_factory=Counter)
    craft_attempted: int = 0
    craft_successful: int = 0
    craft_kept: int = 0
    craft_discarded: int = 0
    
    rests: int = 0
    rest_time: float = 0

    @property
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0

        end = datetime.now() if self.stop_time is None else self.stop_time
        return (end - self.start_time).total_seconds()

    @property
    def xp_per_hour(self, current_xp: int = 0) -> float:
        secs = self.elapsed
        if secs == 0:
            return 0

        if self.end_xp == 0 and current_xp == 0:
            xp_gained = 0
        elif self.end_xp:
            xp_gained = self.end_xp - self.start_xp
        else:
            xp_gained = current_xp - self.start_xp

        return xp_gained / (secs / 3600)

    @property
    def gold_per_hour(self, current_gold: int = 0, current_bank: int = 0) -> float:
        secs = self.elapsed
        if secs == 0:
            return 0

        if self.end_gold == 0 and current_gold == 0:
            gold_gained = 0
        elif self.end_gold:
            gold_gained = self.end_gold - self.start_gold
            gold_gained += self.end_bank - self.start_bank
        else:
            gold_gained = current_gold - self.start_gold
            gold_gained += current_bank - self.start_bank

        return gold_gained / (secs / 3600)
