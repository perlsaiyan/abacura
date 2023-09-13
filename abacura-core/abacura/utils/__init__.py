from numbers import Real
from collections import OrderedDict
import re

_pct_colors = OrderedDict()
_pct_colors[80] = "green"
_pct_colors[60] = "green_yellow"
_pct_colors[40] = "yellow"
_pct_colors[20] = "dark_orange3"
_pct_colors[0]  = "red"

ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def percent_color(cval: Real) -> str:
    for key, value in _pct_colors.items():
        if key < cval:
            return value
    return "dark_red"

def human_format(num) -> str:
    if isinstance(num, str):
        num = int(num)
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
