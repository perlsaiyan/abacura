"""Legends of Kallisti Specific Widgets"""
from __future__ import annotations

import sys
from importlib import import_module
from typing import TYPE_CHECKING

from serum import inject
from textual import log
from textual.widget import Widget

from abacura.plugins import Plugin, CommandError
from abacura_kallisti.atlas.world import World
from abacura_kallisti.atlas.room import ScannedRoom
from abacura_kallisti.plugins.msdp import TypedMSDP
from abacura_kallisti.atlas.location import LocationList
from abacura_kallisti.mud.player import PlayerCharacter

from ..case import camel_to_snake

if TYPE_CHECKING:
    from .lokcomms import LOKComms
    from .queue import LOKQueueRunner, QueueManager


__all__ = [
    "LOKComms",
    "LOKQueueRunner",
    "LOKPlugin"
]

__LOCAL_CLASSES__ = ["LOKPlugin"]


class LOKPlugin(Plugin):
    """Subclass of standard Plugin with additional Kallisti Specifics """

    def __init__(self):
        super().__init__()

        self.msdp: TypedMSDP = self._context['msdp']
        self.world: World = self._context['world']
        self.cq: QueueManager = self._context['cq']
        self.pc: PlayerCharacter = self._context['pc']
        self.locations: LocationList = self._context['locations']
        self.room: ScannedRoom = self._context['room']

    # @staticmethod
    # def parse_direction(direction: str):
    #     matches = [s for s in CARDINAL_DIRECTIONS if s.startswith(direction.lower())]
    #     if len(matches) == 0:
    #         raise CommandError("Invalid direction %s" % direction)
    #     elif len(matches) > 1:
    #         raise CommandError("Ambiguous direction %s" % direction)
    #     return matches[0]
    #
    # def parse_destination(self, destination: str):
    #
    # def parse_vnum(self, vnum: str):
    #     if vnum not in self.world.rooms:
    #         raise CommandError('Unknown room [%s]' % vnum)
    #
    #     return self.world.rooms[vnum]

    def evaluate_value_room(self, submitted_value: str):
        """function to evaluate command arguments that are Rooms / locations"""
        if not self.msdp or not self.locations:
            return

        if submitted_value is None:
            vnum = self.msdp.room_vnum
        # elif submitted_value.lower() == 'guild':
        #     if self.msdp.cls not in GUILDS:
        #         raise CommandError("Guild unknown for class %s" % self.msdp.cls)
        #     vnum = GUILDS[self.msdp.cls]
        else:
            location = self.locations.get_location(submitted_value)
            if location is not None:
                vnum = location.vnum
            else:
                vnum = submitted_value

        if vnum in self.world.rooms:
            return self.world.rooms[vnum]

        raise CommandError(f'Unknown room [{submitted_value}]')


_WIDGETS_LAZY_LOADING_CACHE: dict[str, type[Widget]] = {}


# Let's decrease startup time by lazy loading our Widgets
# We won't _prefix them so they also get picked up by the plugin loader
# We're just doing this for our convenience
def __getattr__(widget_class: str) -> type[Widget]:
    # Skip our local ones
    if widget_class in __LOCAL_CLASSES__:
        log(f"Local class attempt in {sys.modules[__name__]} for {widget_class}")
        return getattr(sys.modules[__name__], widget_class)

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
