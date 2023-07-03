
import importlib
import io

from abacura.plugins import Plugin, command
from rich.table import Table


class Profiler(Plugin):

    def __init__(self):
        super().__init__()
        self.profiler = None
        self.heap = None
        self.guppy = None

    @command()
    def memory(self, baseline: bool = False):
        """Show memory usage"""

        if self.guppy is None:
            try:
                self.guppy = importlib.import_module("guppy")
            except Exception as ex:
                self.session.show_exception(f"[bold red] # ERROR: {repr(ex)}", ex)
                return False

        if self.heap is None:
            self.heap = self.guppy.hpy()

        if baseline:
            self.heap.setref()
            self.session.output('Memory profiler baselined')
        else:
            self.session.output(str(self.heap.heap()))

    @command
    def profile2(self, num_functions: int = 40, disable: bool = False):
        """Python implemented profiler"""
        from abacura.utils import profiler

        if disable:
            profiler.profile_off()
            return

        self.session.output(profiler.p_profiling)
        if not profiler.p_profiling:
            profiler.profile_on()
            self.session.output("ThreadAware Profiler enabled")
            return

        profiler.profile_off()
        stats_dict = profiler.get_profile_stats()

        tbl = Table()
        tbl.add_column("Function")
        tbl.add_column("Calls")
        tbl.add_column("Elapsed")
        tbl.add_column("CPU")
        tbl.add_column("Self Time")
        for pfn in sorted(stats_dict.values(), key=lambda x: x.self_time, reverse=True)[:num_functions]:
            tbl.add_row(pfn.function.get_location(), str(pfn.call_count),
                        format(pfn.elapsed_time, "6.3f"), format(pfn.cpu_time, "6.3f"),
                        format(pfn.self_time, '6.3f'))
        self.output(tbl)

    @command()
    def profile(self, num_functions: int = 40, disable: bool = False, callers: bool = False, _sort: str = 'time'):
        """Use to profile CPU usage by method

            :num_functions How many rows to display
            :disable Disable the profiler
            :callers Show callers
            :_sort Sort by time, cumulative_time, or calls

        """
        import cProfile
        import pstats

        if disable and self.profiler is not None:
            self.profiler.disable()
            self.profiler = None
            self.session.output("Profiler disabled")
            return

        if self.profiler is None:
            # self.profiler = eval('cProfile.Profile()')
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            self.session.output("Profiler enabled")

            return

        stream = io.StringIO()

        sort_by = [s for s in ('time', 'calls', 'cumulative_time') if s.startswith(_sort.lower())]
        if len(sort_by) == 0:
            raise ValueError("Invalid sort option.  Valid values are time, calls, cumulative")
        sort_by = sort_by[0]

        # ps = eval("pstats.Stats(self.profiler, stream=s).sort_stats(sort_by)")
        ps = pstats.Stats(self.profiler, stream=stream).sort_stats(sort_by)
        if callers:
            ps.print_callers(num_functions)
        else:
            ps.print_stats(num_functions)

        self.session.output(stream.getvalue())
