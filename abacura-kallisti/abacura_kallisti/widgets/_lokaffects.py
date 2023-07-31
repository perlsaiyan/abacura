"""Widget to display current Affects and remaining time"""
from typing import Dict

from rich.columns import Columns
#from rich.text import Text

from textual.app import ComposeResult, RenderResult
from textual.reactive import reactive
from textual.widgets import Static


from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event
from abacura.utils.renderables import Text, OutputColors

# TODO one day this will use LOKMSDP for typed/parsed values
#from abacura_kallisti.mud.affect import Affect

class LOKAffectsList(Static):

    affects: dict = {}
    trigger: reactive[int] = reactive[int](0, always_update=True, layout=True)
    

    def __init__(self):
        super().__init__()
        self.msdp: dict[str, str] = {}
        

    def on_mount(self) -> None:
        self.msdp = self.screen.session.core_msdp.values
        self.screen.session.add_listener(self.update_affects)
        self.affects = self.msdp.get("AFFECTS", {})
        self.trigger = 1

    def render(self) -> RenderResult:
        affects = []
        sorted_keys = list(self.affects.keys())
        sorted_keys.sort()
        sorted_dict = {i: self.affects[i] for i in sorted_keys}
        for aff, val in sorted_dict.items():
            affects.append(Text.assemble((f"{aff:15.15s}", "cyan"),
                                         (f"{val:2s}", OutputColors.value)))
        
        return Columns(affects, width=20)

    @event("core.msdp.AFFECTS")
    def update_affects(self, msg: MSDPMessage):
        self.affects = msg.value
        self.trigger = 1

class LOKAffects(Static):
    can_focus_children = False
    
    def compose(self) -> ComposeResult:
        yield Static("Affects", classes="WidgetTitle", markup=True)
        yield LOKAffectsList()
