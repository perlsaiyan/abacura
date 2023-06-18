"""Legends of Kallisti Specific Widgets"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from textual.widget import Widget

from ..case import camel_to_snake

if TYPE_CHECKING:
    from .lokcomms import LOKComms
    from .queue import LOKQueueRunner
    

__all__ = [
    "LOKComms",
    "LOKQueueRunner",
]

_WIDGETS_LAZY_LOADING_CACHE: dict[str, type[Widget]] = {}


# Let's decrease startup time by lazy loading our Widgets
# We won't _prefix them so they also get picked up by the plugin loader
# We're just doing this for our convenience
def __getattr__(widget_class: str) -> type[Widget]:
    try:
        return _WIDGETS_LAZY_LOADING_CACHE[widget_class]
    except KeyError:
        pass

    if widget_class not in __all__:
        raise ImportError(f"Package 'abacura_kallisti.plugins' has no class '{widget_class}'")

    widget_module_path = f".{camel_to_snake(widget_class)}"
    module = import_module(widget_module_path, package="abacura_kallisti.plugins")
    class_ = getattr(module, widget_class)

    _WIDGETS_LAZY_LOADING_CACHE[widget_class] = class_

    return class_
__all__ = [

]