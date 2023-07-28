
import importlib
import io

from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPanel


class Profiler(Plugin):
    """CPU and Memory Profiling"""

    def __init__(self):
        super().__init__()
        self.profiler = None
        self.heap = None
        self.guppy = None

    @command(hide=True)
    def memory(self, baseline: bool = False, gc: bool = False):
        """
        Show memory usage, set memory baseline, and collect garbage

        :param baseline: Set memory baseline for future measurement
        :param gc: Force garbage collection
        """

        if gc:
            import gc
            gc.collect()
            self.session.output("Garbage collected")

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

    @command(hide=True)
    def pyprofile(self, num_functions: int = 40, disable: bool = False):
        """
        Start/Stop Python implemented profiler (slow...)

        :param num_functions: Number of functions do display
        :param disable: turn off the profiler
        """

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

        rows = []
        for pfn in sorted(stats_dict.values(), key=lambda x: x.self_time, reverse=True)[:num_functions]:
            rows.append((pfn.function.get_location(), pfn.call_count,
                         pfn.elapsed_time / 1E9, pfn.cpu_time, pfn.self_time / 1E9))
        tbl = tabulate(rows, headers=("Function", "Calls", "Elapsed", "CPU", "Self Time"))
        self.output(AbacuraPanel(tbl, title="Profiler Results"))

    @command(hide=True)
    def profile(self, num_functions: int = 40, disable: bool = False, callers: bool = False, _sort: str = 'time'):
        """
        Profile CPU usage by method

        :param num_functions: How many rows to display
        :param disable: Disable the profiler
        :param callers: Show callers
        :param _sort: Sort by 'time', 'cumulative_time', or 'calls'
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
            raise CommandError("Invalid sort option.  Valid values are time, calls, cumulative")
        sort_by = sort_by[0]

        # ps = eval("pstats.Stats(self.profiler, stream=s).sort_stats(sort_by)")
        ps = pstats.Stats(self.profiler, stream=stream).sort_stats(sort_by)
        if callers:
            ps.print_callers(num_functions)
        else:
            ps.print_stats(num_functions)

        self.session.output(stream.getvalue())
