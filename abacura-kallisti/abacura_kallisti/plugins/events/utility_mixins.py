"""
Utility Events Mixin

Contains all utility and miscellaneous patterns for the LOK Events system.
This includes experience gain, exhaustion, material swapping, purchases, and NPC interactions.
"""

from abacura.plugins import action
from .messages import (
    ExhaustionMessage, ExperienceGainMessage,
    ItemPurchaseMessage, MaterialGivenMessage
)


class UtilityEventsMixin:
    """Mixin for utility and miscellaneous event handlers"""
    
    # Player state events
    @action(r"^You are exhausted!$")
    def exhaustion(self):
        """Player exhaustion"""
        self.debuglog("info", "Player is exhausted")
        self.dispatch(ExhaustionMessage())

    @action(r"^You earn (\d+) experience points\.$")
    def experience_gained(self, experience: int):
        """Experience gained"""
        self.debuglog("info", f"Gained {experience} experience points")
        self.dispatch(ExperienceGainMessage(amount=experience))

    @action(r"^(?:SolarLight|Sanla|Skuldotr|Heshak|Kelemvor) gives you some (\w+) (hide|bone)$")
    def material_given(self, quality: str, material: str):
        """Material given by NPC"""
        self.debuglog("info", f"NPC gave material: {quality} {material}")
        self.dispatch(MaterialGivenMessage(quality=quality, material=material, giver="npc"))

    # Commerce events
    @action(r"^You now have a bolt of black cloth\.$")
    def item_purchased(self):
        """Item purchased"""
        self.debuglog("info", "Item purchased: black cloth")
        self.dispatch(ItemPurchaseMessage(item="black_cloth"))
