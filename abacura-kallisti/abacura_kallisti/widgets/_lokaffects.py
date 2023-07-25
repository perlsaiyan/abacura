"""Widget to display current Affects and remaining time"""
from typing import Dict

import rich.box as box
from rich.table import Table
from textual.app import ComposeResult, RenderResult
from textual.reactive import reactive
from textual.widgets import Static, DataTable

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

from abacura_kallisti.mud.affect import Affect

class LOKAffects(Static):
    can_focus_children = False
    
    def compose(self) -> ComposeResult:
        yield Static("Affects", classes="WidgetTitle", markup=True)
        self.datatable = DataTable(id="aff_detail", zebra_stripes=True, show_header=False, show_row_labels=False, show_cursor=False)
        
        yield self.datatable

    def on_mount(self) -> None:
        tbl = self.datatable
        tbl.add_column("affect", key="affect")
        tbl.add_column("time", key="time")
        
        self.screen.session.add_listener(self.update_affects)

    @event("core.msdp.AFFECTS")
    def update_affects(self, msg: MSDPMessage):
        self.datatable.clear()
        for aff, val in msg.value.items():
            self.datatable.add_row(aff, val, label=aff)
        self.datatable.sort("affect")

