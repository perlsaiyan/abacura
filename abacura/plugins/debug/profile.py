
import importlib
import io

from abacura.plugins import Plugin, command


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

        stats = []
        for key, value in stats_dict.items():
            fn, filename, linenum = key
            calls, realtime, cputime = value
            stats.append((fn, filename, linenum, calls, realtime, cputime))

        for pfn in sorted(stats, key=lambda x: x[5], reverse=True)[:num_functions]:
            self.output("%60s %6d %7d %6.3f" % (pfn[0], pfn[2], pfn[3], pfn[5]))

    @command()
    def profile(self, num_functions: int = 40, disable: bool = False, callers: bool = False,
                sort_cumulative: bool = False, sort_calls: bool = False):
        """Use to profile CPU usage by method"""
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
        if sort_cumulative:
            sort_by = 'cumulative'
        elif sort_calls:
            sort_by = 'calls'
        else:
            sort_by = 'time'

        # ps = eval("pstats.Stats(self.profiler, stream=s).sort_stats(sort_by)")
        ps = pstats.Stats(self.profiler, stream=stream).sort_stats(sort_by)
        if callers:
            ps.print_callers(num_functions)
        else:
            ps.print_stats(num_functions)

        self.session.output(stream.getvalue())
