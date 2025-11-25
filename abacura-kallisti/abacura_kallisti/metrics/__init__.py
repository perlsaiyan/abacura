from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from collections import Counter


@dataclass(slots=True)
class EarnedXP:
    source: str = ""
    area: str = ""
    vnum: str = ""
    victim: str = ""
    xp: int = 0


@dataclass(slots=True)
class EarnedGold:
    source: str = ""
    area: str = ""
    vnum: str = ""
    victim: str = ""
    gold: int = 0


@dataclass(slots=True)
class KillEvent:
    victim: str = ""
    area: str = ""
    vnum: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MudMetrics:
    mission: str = ""
    character_name: str = ""
    area_name: str = ""
    
    start_time: Optional[datetime] = None  # field(default_factory=datetime.now)
    stop_time: Optional[datetime] = None

    xp_events: List[EarnedXP] = field(default_factory=list)
    gold_events: List[EarnedGold] = field(default_factory=list)
    kill_events: List[KillEvent] = field(default_factory=list)

    counters: Counter = field(default_factory=Counter)
    info: Dict = field(default_factory=dict)

    start_xp: int = 0
    start_gold: int = 0
    start_bank: int = 0

    earned_xp: int = 0
    earned_gold: int = 0

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
    def xp_per_hour(self) -> float:
        secs = self.elapsed
        if secs == 0:
            return 0

        xp_gained = max(self.end_xp - self.start_xp, self.earned_xp)

        return xp_gained / (secs / 3600)

    @property
    def kills_per_hour(self) -> float:
        secs = self.elapsed
        if secs == 0:
            return 0
        return self.kills / (secs / 3600)

    @property
    def kills_per_hour_last_15min(self) -> float:
        if not self.kill_events:
            return 0
        
        now = datetime.now()
        fifteen_minutes_ago = now.timestamp() - (15 * 60)  # 15 minutes in seconds
        
        # Count kills in the last 15 minutes
        recent_kills = sum(1 for kill in self.kill_events 
                          if kill.timestamp.timestamp() >= fifteen_minutes_ago)
        
        # Calculate kills per hour based on 15-minute window
        return recent_kills * 4  # 4 * 15 minutes = 1 hour

    @property
    def gold_per_hour(self) -> float:
        secs = self.elapsed
        if secs == 0:
            return 0

        gold_gained = max(self.end_gold - self.start_gold + self.end_bank - self.start_bank, self.earned_gold)
        return gold_gained / (secs / 3600)

    def earn_xp(self, source: str, xp: int, victim: str = '', area: str = '', vnum: str = ''):
        if self.stop_time is None:
            self.xp_events.append(EarnedXP(source=source, xp=xp, victim=victim, area=area, vnum=vnum))
            self.earned_xp += xp

    def earn_gold(self, source: str, gold: int, victim: str = '', area: str = '', vnum: str = ''):
        if self.stop_time is None:
            self.gold_events.append(EarnedGold(source=source, gold=gold, victim=victim, area=area, vnum=vnum))
            self.earned_gold += gold

    def kill(self, victim: str = '', area: str = '', vnum: str = ''):
        if self.stop_time is None:
            self.kill_events.append(KillEvent(victim=victim, area=area, vnum=vnum))
            self.kills += 1
