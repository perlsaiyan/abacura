from numbers import Real
from collections import OrderedDict
import re

_pct_colors = OrderedDict()
_pct_colors[80] = "green"
_pct_colors[60] = "green_yellow"
_pct_colors[40] = "yellow"
_pct_colors[20] = "dark_orange3"
_pct_colors[-1]  = "red"

ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def percent_color(cval: Real) -> str:
    for key, value in _pct_colors.items():
        if key < cval:
            return value
    return ""
