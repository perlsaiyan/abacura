"""
Crafting Events Mixin

Contains all crafting-related action patterns for the LOK Events system.
This includes basic crafting, specific crafting types, and crafting failures.
"""

from abacura.plugins import action
from .messages import (
    MaterialQuality, CraftedItemMessage, CraftFailureMessage,
    SpecificCraftMessage, PoisonCraftMessage, WeaponForgeMessage, BrewingMessage
)


class CraftingEventsMixin:
    """Mixin for crafting-related event handlers"""
    
    # Basic crafting patterns
    @action(r"^You craft an? (\w+) (shield|robe)\.$")
    def crafting(self, quality: str, output: str):
        """Crafting event"""
        self.debuglog("info", f"Crafted {quality} {output}")
        self.dispatch(CraftedItemMessage(
            success=True,
            quality=MaterialQuality.find(quality),
            output=output
        ))

    @action(r"^You fail to craft anything useful\.$")
    def crafting_failed(self):
        """Crafting failed"""
        self.debuglog("info", "Basic crafting failed")
        self.dispatch(CraftedItemMessage(success=False))

    # Generic crafting success pattern
    @action(r"^You (?:craft|weave|mill|tan|smelt|carve|forge|brew) (?:some |an? )(\w+) (?:.*?)(?:armor|cloth|wood|leather|metal|bone|poison|axe|machete|hammer|maul|lance|dagger|\w+)\.$")
    def crafting_success(self, quality: str):
        """Generic crafting success"""
        self.debuglog("info", f"Generic crafting success: {quality} quality")
        self.dispatch(CraftedItemMessage(
            success=True,
            quality=MaterialQuality.find(quality),
            output="crafted_item"
        ))

    # Generic crafting failure patterns
    @action(r"^You fail to improve it\.")
    def crafting_failure_improve(self):
        """Crafting failure to improve"""
        self.debuglog("Crafting failure to improve","info")
        self.dispatch(CraftFailureMessage(method="crafting", reason="failed"))

    @action(r"^(?:Was that salt or sugar\?|The smell coming from the recipe makes you gag\.|Oops, you cracked it a little\.|You failed to craft anything useful\.?)")
    def crafting_failure(self):
        """Generic crafting failure"""
        self.debuglog("info", "Generic crafting failure")
        self.dispatch(CraftFailureMessage(method="crafting", reason="failed"))

    # Specific crafting success patterns
    @action(r"^You craft some (\w+) poison from (.*) from the corpse of (.*)\.?$")
    def poison_crafted(self, quality: str, _source: str, _source2: str):
        """Poison crafting success"""
        self.debuglog("info", f"Poison crafted: {quality} quality from corpse")
        self.dispatch(PoisonCraftMessage(
            quality=MaterialQuality.find(quality),
            source="corpse"
        ))

    @action(r"^You craft an? (\w+) leather armor made from (.*)\.?$")
    def leather_crafted(self, quality: str, _source: str):
        """Leather armor crafting success"""
        self.debuglog("info", f"Leather armor crafted: {quality} quality")
        self.dispatch(SpecificCraftMessage(
            craft_type="leatherwork",
            quality=MaterialQuality.find(quality),
            output="armor",
            source="leather"
        ))

    @action(r"^You craft an? (\w+) armor\.?$")
    def metal_armor_crafted(self, quality: str):
        """Metal armor crafting success"""
        self.debuglog("info", f"Metal armor crafted: {quality} quality")
        self.dispatch(SpecificCraftMessage(
            craft_type="metalwork", 
            quality=MaterialQuality.find(quality),
            output="armor",
            source="metal"
        ))

    @action(r"^You carve (.*) gigasaur tooth into some (.*) bone from gigasaur\.?$")
    def gigasaur_tooth_carved(self, original_quality: str, new_quality: str):
        """Gigasaur tooth carving"""
        self.debuglog("info", f"Gigasaur tooth carved: {original_quality} -> {new_quality} bone")
        self.dispatch(SpecificCraftMessage(
            craft_type="carving",
            quality=MaterialQuality.find(new_quality),
            original_quality=original_quality,
            output="bone",
            source="gigasaur_tooth"
        ))

    @action(r"^You carve some (\w+) bone from (.*)\.?$")
    def bone_carved(self, quality: str, _source: str):
        """Bone carving success"""
        self.debuglog(f"Bone carved: {quality} quality","info")
        self.dispatch(SpecificCraftMessage(
            craft_type="carving",
            quality=MaterialQuality.find(quality),
            output="bone",
            source="bone"
        ))

    @action(r"^You (smoke|cook|roast|grill) some (.*) (meat from .*) into some (.*) (jerky|stew|roast|steak)\.?$")
    def meat_cooked(self, method: str, _original: str, _source: str, _quality: str, output: str):
        """Meat cooking success"""
        self.debuglog("info", f"Meat cooked: {method} -> {output}")
        self.dispatch(SpecificCraftMessage(
            craft_type="cooking",
            quality=MaterialQuality.AVERAGE,  # Default for cooked items
            output=output,
            source="meat"
        ))

    @action(r"^You weave some (\w+) (cotton|silk) into an? (\w+) cloth\.?$")
    def fabric_woven(self, original_quality: str, fabric: str, quality: str):
        """Fabric weaving success"""
        self.debuglog("info", f"Fabric woven: {original_quality} {fabric} -> {quality} cloth")
        self.dispatch(SpecificCraftMessage(
            craft_type="weaving",
            quality=MaterialQuality.find(quality),
            original_quality=original_quality,
            output="cloth",
            source=fabric
        ))

    @action(r"^You mill some (\w+) wood into an? (\w+) milled wood\.?$")
    def wood_milled(self, original_quality: str, quality: str):
        """Wood milling success"""
        self.debuglog("info", f"Wood milled: {original_quality} -> {quality} milled wood")
        self.dispatch(SpecificCraftMessage(
            craft_type="milling",
            quality=MaterialQuality.find(quality),
            original_quality=original_quality,
            output="milled_wood",
            source="wood"
        ))

    @action(r"^You tan some (.*) (?:hide from .*) into some (.*) (leather) from.*$")
    def hide_tanned(self, original_quality: str, quality: str, output: str):
        """Hide tanning success"""
        self.debuglog("info", f"Hide tanned: {original_quality} -> {quality} {output}")
        self.dispatch(SpecificCraftMessage(
            craft_type="tanning",
            quality=MaterialQuality.find(quality),
            original_quality=original_quality,
            output=output,
            source="hide"
        ))

    @action(r"^You smelt some (.*) (?:ore) into an? (.*) (metal)\.?$")
    def ore_smelted(self, original_quality: str, quality: str, output: str):
        """Ore smelting success"""
        self.debuglog("info", f"Ore smelted: {original_quality} -> {quality} {output}")
        self.dispatch(SpecificCraftMessage(
            craft_type="smelting",
            quality=MaterialQuality.find(quality),
            original_quality=original_quality,
            output=output,
            source="ore"
        ))

    @action(r"^You brew an? (.*)\.?$")
    def potion_brewed(self, potion: str):
        """Brewing/potion creation"""
        self.debuglog("info", f"Potion brewed: {potion}")
        self.dispatch(BrewingMessage(potion_type=potion))

    @action(r"^You forge an? (.*) (axe|machete|hammer|maul|lance)\.?$")
    def weapon_forged(self, quality: str, weapon: str):
        """Weapon forging success"""
        self.debuglog("info", f"Weapon forged: {quality} {weapon}")
        self.dispatch(WeaponForgeMessage(
            quality=MaterialQuality.find(quality),
            weapon_type=weapon
        ))

    @action(r"^You craft an? (.*) dagger made from (.*)\.?$")
    def dagger_crafted(self, quality: str, source: str):
        """Dagger crafting success"""
        self.debuglog("info", f"Dagger crafted: {quality} quality from {source}")
        self.dispatch(SpecificCraftMessage(
            craft_type="weaponcraft",
            quality=MaterialQuality.find(quality),
            output="dagger",
            source=source
        ))
