from __future__ import annotations

from typing import TYPE_CHECKING

from textual import log
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static, ProgressBar

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

from abacura_kallisti.mud.experience import LEVEL_VALUES

if TYPE_CHECKING:
    from abacura import Session
    from abacura_kallisti.screens import KallistiScreen
    from typing import Self

class LOKExperience(Static):

    my_reactives = {
        "LEVEL": "c_level",
        "EXPERIENCE": "c_exp",
        "EXPERIENCE_TNL": "c_exp_tnl",
        "HERO_POINTS": "c_hero_points",
        "HERO_POINTS_TNL": "c_hero_points_tnl",
        "REMORT_LAPS_TOTAL": "c_remorts",
        "REMORT_LAPS_IN_CLASS": "c_laps_in_class",
    }

    c_level: reactive[int] = reactive[int](0)
    c_exp: reactive[int] = reactive[int](0)
    c_exp_tnl: reactive[int] = reactive[int](0)
    c_hero_points: reactive[int] = reactive[int](0)
    c_hero_points_tnl: reactive[int] = reactive[int](0)
    c_remorts: reactive[int] = reactive[int](0)
    c_laps_in_class: reactive[int] = reactive[int](0)

    def __init__(self, **kwargs):
        super().__init__()
        self.remort_line = Static(id="remorts")

    def setup_progress_bars(self):
        self.pb_xp = ProgressBar(id="xp_to_level", classes="LOKProgBar", show_eta=True, show_percentage=True)
        self.pb_xpsack = ProgressBar(id="xp_to_sack", classes="LOKProgBar", show_eta=True, show_percentage=True)
        self.pb_herp = ProgressBar(id="herp_to_level", classes="LOKProgBar", show_eta=True, show_percentage=True)
        self.mount(self.pb_xp, after=self.query_one("#levelxplabel"))
        self.mount(self.pb_xpsack, after=self.query_one("#capxplabel"))
        self.mount(self.pb_herp, after=self.query_one("#herplabel"))

    def compose(self) -> ComposeResult:
        yield Static("Experience", classes="WidgetTitle")
        yield self.remort_line
        yield Static("[cyan]XP to Level", id="levelxplabel")
        yield Static("[cyan]XP to Cap", id="capxplabel")
        yield Static("[cyan]Heros to Level", id="herplabel")
        

    def on_mount(self):
        """Set up listeners, update visibility state"""
        self.screen.session.add_listener(self.update_reactives)
        self.setup_progress_bars()
        if not self.c_level:
            self.display = False

    @event("core.msdp")
    def update_reactives(self, message: MSDPMessage):
        """Update reactive values for this widget"""
        
        if message.subtype in self.my_reactives:
            setattr(self, self.my_reactives[message.subtype], int(message.value))
            self.remort_line.update(f"[cyan]Remorts: [white]{self.c_remorts} [cyan]In Class: [white]{self.c_laps_in_class}")

            if message.subtype in ["LEVEL"]:
                # Update progress bar totals based on new level
                # No need to recreate the progress bars

                # no need to progress
                if self.c_level > 199:
                    self.display = False
                    return                

                if self.c_level > 99:
                    self.query_one("#levelxplabel").display = False
                    self.pb_xp.display = False
                    self.query_one("#herplabel").display = False
                    self.pb_herp.display = False

                # Update progress bar totals for the new level
                if self.c_level > 19 and self.c_level < 95:
                    self.pb_xpsack.total = LEVEL_VALUES[self.c_level + 1].xp * 5
                else:
                    self.pb_xpsack.total = pow(2,32) - 1
                    
                # Update XP progress bar total
                self.pb_xp.total = int(self.c_exp) + int(self.c_exp_tnl)
                
                # Update hero points progress bar total
                self.pb_herp.total = self.c_hero_points + self.c_hero_points_tnl
                    
                return

            if message.subtype in ["EXPERIENCE", "EXPERIENCE_TNL"]:
                self.pb_xp.total = int(self.c_exp) + int(self.c_exp_tnl)
                self.pb_xp.progress = self.c_exp
                self.pb_xpsack.progress = self.c_exp

            if message.subtype in ["HERO_POINTS", "HERO_POINTS_TNL"]:
                self.pb_herp.total = self.c_hero_points + self.c_hero_points_tnl
                self.pb_herp.progress = self.c_hero_points

        if not self.display and self.c_level < 200:
            self.display = True
