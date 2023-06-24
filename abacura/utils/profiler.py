from time import time
import threading
import sys
from collections import deque
try:
    from resource import getrusage, RUSAGE_SELF
except ImportError:
    RUSAGE_SELF = 0
    def getrusage(who=0):
        return [0.0, 0.0] # on non-UNIX platforms cpu_time always 0.0

p_stats = None
p_start_time = None
p_profiling = False

def profiler(frame, event, arg):
    if event not in ('call','return'): return profiler
    #### gather stats ####
    rusage = getrusage(RUSAGE_SELF)
    t_cpu = rusage[0] + rusage[1] # user time + system time
    code = frame.f_code
    fun = (code.co_name, code.co_filename, code.co_firstlineno)
    #### get stack with functions entry stats ####
    ct = threading.current_thread()
    try:
        p_stack = ct.p_stack
    except AttributeError:
        ct.p_stack = deque()
        p_stack = ct.p_stack
    #### handle call and return ####
    if event == 'call':
        p_stack.append((time(), t_cpu, fun))
    elif event == 'return':
        try:
            t,t_cpu_prev,f = p_stack.pop()
            assert f == fun
        except IndexError: # TODO investigate
            t,t_cpu_prev,f = p_start_time, 0.0, None
        call_cnt, t_sum, t_cpu_sum = p_stats.get(fun, (0, 0.0, 0.0))
        p_stats[fun] = (call_cnt+1, t_sum+time()-t, t_cpu_sum+t_cpu-t_cpu_prev)
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


def get_profile_stats():
    """
    returns dict[function_tuple] -> stats_tuple
    where
      function_tuple = (function_name, filename, lineno)
      stats_tuple = (call_cnt, real_time, cpu_time)
    """
    return p_stats
