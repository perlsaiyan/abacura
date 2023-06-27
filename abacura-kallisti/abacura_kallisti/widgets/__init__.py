"""Legends of Kallisti Specific Widgets"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from textual.widget import Widget

from ..case import camel_to_snake

if TYPE_CHECKING:
    from ._lokcharacter import LOKCharacter
    from ._lokexperience import LOKExperience
    from ._indeterminate_progress_bar import IndeterminateProgressBar
    from ._lokleft import LOKLeft
    from ._lokright import LOKRight
    from ._lokmap import LOKMap
    from ._lokzone import LOKZone
    from ._lokgroup import LOKGroup
    

__all__ = [
    "LOKCharacter",
    "LOKExperience",
    "LOKLeft",
    "LOKMap",
    "LOKRight",
    "LOKZone",
    "LOKGroup",
    "IndeterminateProgressBar",
]

_WIDGETS_LAZY_LOADING_CACHE: dict[str, type[Widget]] = {}


# Let's decrease startup time by lazy loading our Widgets:
def __getattr__(widget_class: str) -> type[Widget]:
    try:
        return _WIDGETS_LAZY_LOADING_CACHE[widget_class]
    except KeyError:
        pass

    if widget_class not in __all__:
        raise ImportError(f"Package 'abacura_kallisti.widgets' has no class '{widget_class}'")

    widget_module_path = f"._{camel_to_snake(widget_class)}"
    module = import_module(widget_module_path, package="abacura_kallisti.widgets")
    class_ = getattr(module, widget_class)

    _WIDGETS_LAZY_LOADING_CACHE[widget_class] = class_

    return class_