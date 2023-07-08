"""Widget to display current Affects and remaining time"""
from typing import Dict

import rich.box as box
from rich.table import Table
from textual.app import ComposeResult, RenderResult
from textual.reactive import reactive
from textual.widgets import Static, DataTable

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

from abacura_kallisti.plugins.msdp import Affect

class LOKAffects(Static):
    def compose(self) -> ComposeResult:
        yield Static("Affects", classes="WidgetTitle", markup=True)
        #yield LOKAffectDetail()
        self.datatable = DataTable(id="aff_detail", zebra_stripes=True, show_header=False, show_row_labels=False, show_cursor=False)
        self.datatable.can_focus = False
        yield self.datatable

    def on_mount(self) -> None:
        tbl = self.datatable
        tbl.add_column("affect", key="affect")
        tbl.add_column("time", key="time")
        
        self.screen.session.listener(self.update_affects)

    @event("core.msdp.AFFECTS")
    def update_affects(self, msg: MSDPMessage):
        self.datatable.clear()
        for aff, val in msg.value.items():
            self.datatable.add_row(aff, val, label=aff)
        self.datatable.sort("affect")






class LOKAffectDetail(Static):
    """Widget to display affects and duration"""
    affects: reactive[Dict[str, str] | None] = reactive[Dict[str, str] | None](None)

    def render(self) -> RenderResult:
        tbl = Table(show_header=False,show_edge=False,show_lines=False, box=box.SIMPLE,expand=True)
        tbl.pad_edge = False
        if not self.affects:
            return Table.grid()
        
        tbl.add_column()
        tbl.add_column()
        tbl.add_column()
        tbl.add_column()

        affs = list(self.affects.items())

        if (len(affs) % 2 ) > 0:
            affs.append(("",""))
    
        for x in range(0, len(affs)-1, 2):
            chunk = affs[x:x+2]
            row = [chunk[0][0], chunk[0][1], chunk[1][0], chunk[1][1]]            
            tbl.add_row(*row)
        return tbl

    def on_mount(self) -> None:
        self.screen.session.listener(self.update_affects)
    
    @event("core.msdp.AFFECTS")
    def update_affects(self, msg: MSDPMessage):
        self.affects = self.screen.session.core_msdp.values["AFFECTS"]
