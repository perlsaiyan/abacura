from time import monotonic
from rich.table import Table
from rich.panel import Panel
from typing import Dict, Optional

from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.plugins.queue import QueueTask

from abacura.plugins import command

class AutoBuf(LOKPlugin):
    """Handle application of bufs"""
    _RUNNER_INTERVAL: float = 2.0
    _RENEWABLE_BUFS = ["true seeing", "sanctuary"]
    _EXPIRING_BUFS = []
    def __init__(self):
        super().__init__()
        self.last_attempt: Dict[str, float] = {}
        # Gods don't need bufs :)
        if self.msdp.level < 200:
            self.add_ticker(self._RUNNER_INTERVAL, callback_fn=self.bufcheck, repeats=-1, name="Autobuf")

    def bufcheck(self):
        """Ticker to loop through all the buffs we know of, and renew or add ones we need"""
        for buf in self._RENEWABLE_BUFS:
            if self.msdp.get_affect_hours(buf) < 2:
                self.acquire_buf(buf)
        for buf in self._EXPIRING_BUFS:
            if self.msdp.get_affect_hours(buf) < 1:
                self.acquire_buf(buf)             

    def acquire_buf(self, buf):
        """Figure out how to get buf and if possible, acquire it"""
        # Only try once every 10 seconds
        if monotonic() - self.last_attempt.get(buf,0) > 10:
            self.last_attempt[buf] = monotonic()
            method = self.acquisition_method(buf)
            
            if method:
                
                self.cq.add(QueueTask(f"say Acquiring {buf}", 1.0),"NCO")
            #else:
            #    self.output(f"[bold red]# AUTOBUF: No method of acquisition for {buf}!", markup=True)    

    def acquisition_method(self, spell: str) -> Optional[str]:
        """Returns likely acquisition method"""
        return None
    
    @command(name="autobuf")
    def list_autobufs(self):
        """Show known buffs, will add current or expected buffs or something"""
        tbl = Table(title="Known Buff Affects")
        tbl.add_column("Buff")
        tbl.add_column("Hours Left")
        tbl.add_column("AcquisitionMethod")
        
        for buf in [*self._EXPIRING_BUFS, *self._RENEWABLE_BUFS]:
            remaining = self.msdp.get_affect_hours(buf)
            if remaining > 5:
                tbl.add_row(buf, str(remaining), self.acquisition_method(buf) or "None", style="green")
            elif remaining > 0:
                tbl.add_row(buf, str(remaining), self.acquisition_method(buf) or "None", style="yellow")
            elif self.acquisition_method(buf):
                tbl.add_row(buf, "-", self.acquisition_method(buf) or "None", style="orange1")
            else:
                tbl.add_row(buf, "-", self.acquisition_method(buf) or "None", style="red")
        self.output(Panel(tbl), actionable=False)
