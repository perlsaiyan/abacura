from dataclasses import fields, is_dataclass, astuple
from itertools import zip_longest
from rich.table import Table
from typing import Iterable


def tabulate(tabular_data, headers=(), float_format="9.3f", **kwargs):
    """
    Create a rich Table with automatic justification for numbers and a configurable floating point format.

    tabular_data can be a List[List], List[Dict], List[Tuple], List[dataclass], List[str]
    headers should be an interable list/tuple of header names
    kwargs are passed through to rich Table

    """
    # title="", title_justify="left", title_style=None,
    # caption="", caption_justify="left", caption_style=None,
    # header_style=None, border_style=None,

    tbl = Table(**kwargs)

    if isinstance(headers, str):
        headers = [headers]

    if len(tabular_data) == 0:
        if len(headers) == 0:
            return tbl
        column_types = [str for _ in headers]
    elif isinstance(tabular_data[0], dict):
        keys = tabular_data[0].keys()
        headers = headers if len(headers) else list(keys)
        tabular_data = [[row.get(k, None) for k in keys] for row in tabular_data]
        column_types = [type(v) for v in tabular_data[0]]
    elif is_dataclass(tabular_data[0]):
        df = fields(tabular_data[0])
        headers = headers if len(headers) else list([f.name for f in df])
        tabular_data = [astuple(row) for row in tabular_data]
        column_types = [f.type for f in df]
    elif not isinstance(tabular_data[0], Iterable) or isinstance(tabular_data[0], str):
        tabular_data = [[row] for row in tabular_data]
        column_types = [type(v) for v in tabular_data[0]]
    else:
        column_types = [type(v) for v in tabular_data[0]]

    for h, ct in zip_longest(headers, column_types):
        if h and h.startswith("_"):
            justify = "right"
        elif ct in (int, 'int', float, 'float'):
            justify = "right"
        else:
            justify = "left"
        tbl.add_column(header=h.lstrip("_") or "", justify=justify)

    for row in tabular_data:
        values = [format(v, float_format) if ct in (float, "float") else str(v) for ct, v in zip(column_types, row)]
        tbl.add_row(*values)

    return tbl
