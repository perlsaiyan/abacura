"""
Harvest Events Mixin

Contains all harvest-related action patterns for the LOK Events system.
This includes mining, logging, gathering, butchering, skinning, and prospecting.
"""

from abacura.plugins import action
from .messages import (
    Material, MaterialQuality, HarvestMessage, ProspectMessage,
    MaterialFoundMessage, LowQualityMaterialMessage
)


class HarvestEventsMixin:
    """Mixin for harvest-related event handlers"""
    
    # Basic harvest patterns
    @action(r"^You can't seem to find anything\.$")
    def no_harvest(self):
        """No harvestable resources found"""
        self.debuglog("info", "No harvestable resources found")
        self.dispatch(HarvestMessage(success=False))

    @action(r"^You (mine|gather|chop down) some (\w+) (herbs|ore|wood)\.$")
    def harvesting_success(self, _verb: str, quality: str, material: str):
        """Successful harvesting attempt, dispatch HarvestMessage"""
        mq = MaterialQuality.find(quality)
        
        material_type = Material.NONE
        match material:
            case "ore":
                material_type = Material.ORE
            case "herbs":
                material_type = Material.HERB
            case "wood":
                material_type = Material.WOOD

        harvest_msg = HarvestMessage(
            success=True,
            quality=mq,
            material=material_type
        )
        self.debuglog("info", f"Harvested {quality} {material} -> {material_type.value}")
        self.dispatch(harvest_msg)

    @action(r"^You (search|look|prospect) for (decent fibers|the good stuff|good timber|decent ore veins) nearby\.\.\.$")
    def prospecting_action(self, method: str, material: str):
        """Fire a prospecting event"""
        self.debuglog("info", f"Prospecting: {method} for {material}")
        self.dispatch(ProspectMessage(method=method, material=material))

    @action(r"^There's nothing to mine here\.$")
    def mining_failed(self):
        """Mining failed, look for more"""
        self.debuglog("info", "Mining failed - nothing to mine here")
        self.dispatch(HarvestMessage(success=False))

    # Material scavenging patterns
    @action(r"^Some (bone|hide|meat) from a .* lies here\.$")
    def material_found(self, material: str):
        """Material found on ground for scavenging"""
        self.debuglog("info", f"Material found on ground: {material}")
        self.dispatch(MaterialFoundMessage(material=material))

    @action(r"^The some (?:\w+) (herbs|cotton|meat.*|hide.*|bone.*) isn't high enough quality to")
    def low_quality_material(self, material: str):
        """Low quality material detected"""
        # Extract base material type
        base_material = material.split()[0] if " " in material else material
        self.debuglog("info", f"Low quality material detected: {base_material}")
        self.dispatch(LowQualityMaterialMessage(material=base_material, quality="low"))

    # Advanced harvest patterns (butcher, skin, etc.)
    @action(r"^You (butcher|skin|extract|gather) some (\w+)( quality)? (\w+)( from (.*))?\.?$")
    def material_harvested(self, method: str, quality: str, _quality_word: str, output: str, _from: str, source: str):
        """Material harvesting success"""
        material_type = Material.NONE
        match output:
            case "hide":
                material_type = Material.HIDE
            case "meat":
                material_type = Material.MEAT  
            case "bone":
                material_type = Material.BONE
            case "herbs" | "herb":
                material_type = Material.HERB
            case "cotton":
                material_type = Material.COTTON

        harvest_msg = HarvestMessage(
            success=True,
            quality=MaterialQuality.find(quality),
            material=material_type
        )
        self.debuglog(f"Material harvested: {method} -> {quality} {output}", "info")
        self.dispatch(harvest_msg)

    @action(r"^You (butcher|skin) it but you make a mess of it\.$")
    def harvest_failure(self, method: str):
        """Butcher or skinning failure"""
        self.debuglog("info", f"Harvest failure: {method} made a mess")
        self.dispatch(HarvestMessage(success=False))

    # Low quality material sacrifice patterns
    @action(r"^The (?:some (\w+) wood|a bolt of (\w+) cloth|a (\w+) gigasaur tooth) isn't high enough quality to (?:mill|be worth crafting|carve)\.$")
    def low_quality_sacrifice_needed(self, wood_quality: str, cloth_quality: str, tooth_quality: str):
        """Low quality material needs sacrificing"""
        if wood_quality:
            self.debuglog("info", f"Low quality wood needs sacrificing: {wood_quality}")
            self.dispatch(LowQualityMaterialMessage(material="wood", quality=wood_quality))
        elif cloth_quality:
            self.debuglog("info", f"Low quality cloth needs sacrificing: {cloth_quality}")
            self.dispatch(LowQualityMaterialMessage(material="cloth", quality=cloth_quality))
        elif tooth_quality:
            self.debuglog("info", f"Low quality tooth needs sacrificing: {tooth_quality}")
            self.dispatch(LowQualityMaterialMessage(material="tooth", quality=tooth_quality))
