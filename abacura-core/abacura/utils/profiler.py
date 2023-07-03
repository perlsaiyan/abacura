from time import time
from dataclasses import dataclass
import threading
import sys
from collections import deque
from typing import Dict

try:
    from resource import getrusage, RUSAGE_SELF
except ImportError:
    RUSAGE_SELF = 0


    def getrusage(_who=0):
        return [0.0, 0.0]  # on non-UNIX platforms cpu_time always 0.0


@dataclass(slots=True, frozen=True, eq=True)
class Function:
    co_name: str = ''
    co_filename: str = ''
    co_first_lineno: int = 0

    def get_location(self) -> str:
        return f"{self.co_filename}:{self.co_name}[{self.co_first_lineno}]"


@dataclass(slots=True)
class FunctionStats:
    function: Function
    call_count: int = 0
    elapsed_time: float = 0
    cpu_time: float = 0
    child_time: float = 0
    child_cpu_time: float = 0

    @property
    def self_time(self) -> float:
        return self.elapsed_time - self.child_time

    @property
    def self_cpu_time(self) -> float:
        return self.cpu_time - self.child_cpu_time


@dataclass(slots=True)
class FunctionCall:
    function: Function = Function()
    start_time: float = 0
    start_cpu_time: float = 0
    child_time: float = 0
    child_cpu_time: float = 0


p_stats: Dict[Function, FunctionStats] = {}
p_start_time = None
p_profiling = False


def profiler(frame, event, _arg):
    global p_stats
    if event not in ('call', 'return'):
        return profiler

    # gather stats
    rusage = getrusage(RUSAGE_SELF)
    t_cpu = rusage[0] + rusage[1]  # user time + system time
    code = frame.f_code
    function = Function(code.co_name, code.co_filename, code.co_firstlineno)

    # get stack with functions entry stats
    ct = threading.current_thread()
    try:
        p_stack = ct.p_stack
    except AttributeError:
        ct.p_stack = deque()
        p_stack = ct.p_stack

    # handle call and return #
    if event == 'call':
        p_stack.append(FunctionCall(function, time(), t_cpu))
        return profiler

    # return
    try:
        function_call: FunctionCall = p_stack.pop()
        assert function_call.function == function
    except IndexError:
        # TODO investigate
        return profiler

    if function in p_stats:
        function_stats = p_stats[function]
    else:
        function_stats = FunctionStats(function)
        p_stats[function] = function_stats

    call_time = time() - function_call.start_time
    cpu_time = t_cpu - function_call.start_cpu_time
    function_stats.call_count += 1
    function_stats.elapsed_time += call_time
    function_stats.cpu_time += cpu_time
    function_stats.child_time += function_call.child_time
    function_stats.child_cpu_time += function_call.child_cpu_time

    if len(p_stack):
        parent: FunctionCall = p_stack[-1]
        parent.child_time += call_time
        parent.child_cpu_time += cpu_time

    return profiler


def profile_on():
    global p_stats, p_start_time, p_profiling
    p_stats = {}
    p_start_time = time()
    threading.setprofile(profiler)
    sys.setprofile(profiler)
    p_profiling = True


def profile_off():
    global p_profiling
    threading.setprofile(None)
    sys.setprofile(None)
    p_profiling = False


def get_profile_stats() -> Dict[Function, FunctionStats]:
    """
    returns dict[Function] -> FunctionStats
    """
    return p_stats
