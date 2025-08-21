"""
LOK Events Message Types

Event message dataclasses for the Lands of Kallisti MUD event system.
All event messages extend AbacuraMessage and define the data structure
for specific game events.
"""
from dataclasses import dataclass
from enum import Enum

from abacura.plugins.events import AbacuraMessage


class Material(Enum):
    """Materials found in the game world"""
    NONE = "none"
    ORE = "ore"
    HERB = "herb"
    COTTON = "cotton"
    SILK = "silk"
    WOOD = "wood"
    FISH = "fish"
    MEAT = "meat"
    BONE = "bone"
    HIDE = "hide"
    MAGIC = "magic"
    GEM = "gem"

    @staticmethod
    def find(material: str):
        """Find a material by name"""
        for m in Material:
            if m.name.lower() == material.lower():
                return m

        if material == "herbs":
            return Material.HERB

        return Material.NONE


class MaterialQuality(Enum):
    """Material quality levels"""
    NONE = 0
    ROUGH = 1
    JUNK = 2
    AVERAGE = 3
    GOOD = 4
    EXCELLENT = 5
    SUPERIOR = 6
    PRISTINE = 7
    EXQUISITE = 8
    FLAWLESS = 9
    DIVINE = 10

    @property
    def craftable(self):
        """Is this material quality craftable?"""
        return self.value >= MaterialQuality.AVERAGE.value

    @staticmethod
    def find(quality: str):
        """Find a quality by name"""
        for q in MaterialQuality:
            if q.name.lower() == quality.lower():
                return q
        return MaterialQuality.NONE


# Basic game event messages
@dataclass
class BeckonMessage(AbacuraMessage):
    """Someone beckons you to follow"""
    event_type: str = "lok.beckon"
    leader: str = ""


@dataclass
class DeathMessage(AbacuraMessage):
    """Player death event"""
    event_type: str = "lok.death"
    room: str = ""


@dataclass
class GetItemMessage(AbacuraMessage):
    """Item retrieval event"""
    event_type: str = "lok.get_item"
    item: str = ""
    container: str = ""
    in_inventory: bool = False


@dataclass
class ArrivalMessage(AbacuraMessage):
    """Player/NPC arrival event"""
    event_type: str = "lok.arrival"
    name: str = ""
    portal: str = ""


@dataclass
class ExhaustionMessage(AbacuraMessage):
    """Player exhaustion event"""
    event_type: str = "lok.exhaustion"


@dataclass
class ExperienceGainMessage(AbacuraMessage):
    """Experience gained event"""
    event_type: str = "lok.experience_gain"
    amount: int = 0


# Material and harvesting event messages
@dataclass
class HarvestMessage(AbacuraMessage):
    """Harvesting Events"""
    event_type: str = "lok.harvest"
    success: bool = False
    quality: MaterialQuality = MaterialQuality.NONE
    material: Material = Material.NONE


@dataclass
class ProspectMessage(AbacuraMessage):
    """Prospecting Event Message"""
    event_type: str = "lok.prospect"
    material: str = ""
    method: str = ""


@dataclass
class MaterialFoundMessage(AbacuraMessage):
    """Material found on ground (scavenging)"""
    event_type: str = "lok.material_found"
    material: str = ""


@dataclass
class LowQualityMaterialMessage(AbacuraMessage):
    """Low quality material detected"""
    event_type: str = "lok.low_quality_material"
    material: str = ""
    quality: str = ""


@dataclass
class MaterialGivenMessage(AbacuraMessage):
    """Material given by NPC"""
    event_type: str = "lok.material_given"
    quality: str = ""
    material: str = ""
    giver: str = ""


# Crafting event messages
@dataclass
class CraftedItemMessage(AbacuraMessage):
    """Crafting Event"""
    event_type: str = "lok.crafted_item"
    success: bool = False
    quality: MaterialQuality = MaterialQuality.NONE
    output: str = ""


@dataclass
class CraftFailureMessage(AbacuraMessage):
    """Crafting failure event"""
    event_type: str = "lok.craft_failure"
    method: str = ""
    reason: str = ""


@dataclass
class SpecificCraftMessage(AbacuraMessage):
    """Specific crafting result (with detailed info)"""
    event_type: str = "lok.specific_craft"
    craft_type: str = ""  # leather, metal, carving, cooking, etc.
    quality: MaterialQuality = MaterialQuality.NONE
    output: str = ""
    original_quality: str = ""
    source: str = ""


@dataclass
class PoisonCraftMessage(AbacuraMessage):
    """Poison crafting result"""
    event_type: str = "lok.poison_craft"
    quality: MaterialQuality = MaterialQuality.NONE
    source: str = ""


@dataclass
class WeaponForgeMessage(AbacuraMessage):
    """Weapon forging result"""
    event_type: str = "lok.weapon_forge"
    quality: MaterialQuality = MaterialQuality.NONE
    weapon_type: str = ""


@dataclass
class BrewingMessage(AbacuraMessage):
    """Brewing/potion creation result"""
    event_type: str = "lok.brewing"
    potion_type: str = ""


# Mount event messages
@dataclass
class MountEvent(AbacuraMessage):
    """Mount/dismount/failure event"""
    event_type: str = "lok.mount"
    target: str = ""
    is_mount: bool = True  # True for mount, False for dismount
    is_failure: bool = False  # True for mount failures (e.g., "Mount what?")


# Utility event messages
@dataclass
class ItemPurchaseMessage(AbacuraMessage):
    """Item purchase event"""
    event_type: str = "lok.item_purchase"
    item: str = ""
