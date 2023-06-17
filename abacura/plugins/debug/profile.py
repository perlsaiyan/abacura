import cProfile
import importlib
import io
import pstats

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

    @command()
    def profile(self, num_functions: int = 40, disable: bool = False, callers: bool = False,
                sort_cumulative: bool = False, sort_calls: bool = False):
        """Use to profile CPU usage by method"""
        # importlib.import_module('cProfile')
        # importlib.import_module('pstats')

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
