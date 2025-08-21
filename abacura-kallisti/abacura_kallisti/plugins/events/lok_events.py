"""
LOK Events Module

Main event handler class that combines all event mixins.
Centralizes game event handling and generation for the Legends of Kallisti MUD.
"""

from abacura_kallisti.plugins import LOKPlugin

from .harvest_mixins import HarvestEventsMixin
from .crafting_mixins import CraftingEventsMixin
from .movement_mixins import MovementEventsMixin
from .utility_mixins import UtilityEventsMixin
from .mount_mixins import MountEventsMixin


class LOKEvents(LOKPlugin, HarvestEventsMixin, CraftingEventsMixin, MovementEventsMixin, UtilityEventsMixin, MountEventsMixin):
    """
    Legends of Kallisti Events Plugin
    
    Combines all event handling mixins to provide comprehensive game event detection
    and dispatching for harvesting, crafting, movement, and utility activities.
    
    This class inherits action handlers from:
    - HarvestEventsMixin: Harvest, mining, gathering, material detection
    - CraftingEventsMixin: All crafting activities and failures
    - MovementEventsMixin: Player/NPC arrivals, deaths, item interactions
    - UtilityEventsMixin: Experience, exhaustion, purchases, NPC gifts
    - MountEventsMixin: Mount and dismount events
    """
    pass