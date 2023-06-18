"""Legends of Kallisti Specific Widgets"""
from __future__ import annotations

from importlib import import_module
import sys
from typing import TYPE_CHECKING

from textual import log
from textual.widget import Widget

from abacura.plugins import Plugin

from ..case import camel_to_snake

if TYPE_CHECKING:
    from .lokcomms import LOKComms
    from .queue import LOKQueueRunner
    

__all__ = [
    "LOKComms",
    "LOKQueueRunner",
    "LOKPlugin"
]

__LOCAL_CLASSES__ = [ "LOKPlugin" ]

class LOKPlugin(Plugin):
    """Subclass of standard Plugin to allow insertion of Kallisti """

    def __init__(self):
        super().__init__()


_WIDGETS_LAZY_LOADING_CACHE: dict[str, type[Widget]] = {}

# Let's decrease startup time by lazy loading our Widgets
# We won't _prefix them so they also get picked up by the plugin loader
# We're just doing this for our convenience
def __getattr__(widget_class: str) -> type[Widget]:
    # Skip our local ones
    if widget_class in __LOCAL_CLASSES__:
        log(f"Local class attempt in {sys.modules[__name__]} for {widget_class}")
        return getattr(sys.modules[__name__],widget_class)
        

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