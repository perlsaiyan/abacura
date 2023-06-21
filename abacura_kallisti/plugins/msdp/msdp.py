"""LOK MSDP plugin"""
from __future__ import annotations

from dataclasses import asdict

from rich.panel import Panel
from rich.pretty import Pretty

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import command
from abacura.plugins.events import event
from abacura_kallisti.plugins import LOKPlugin

MSDP_MAP = {
    "REPORTABLE_VARIABLES": "reportable_variables",
    "CHARACTER_NAME": "name",
    "LEVEL": "level",
    "CLASS": "cls",
    "RACE": "race",
    "HEALTH": "hp",
    "HEALTH_MAX": "hp_max",
    "MANA": "mp",
    "MANA_MAX": "mp_max",
    "STAMINA": "sp",
    "STAMINA_MAX": "sp_max",
    "EXPERIENCE": "xp",
    "COMBAT_STANCE": "stance",
    "RANGED": "ranged",
    "POSITION": "position",
    "OPPONENT_LEVEL": "opponent_level",
    "OPPONENT_NAME": "opponent_name",
    "OPPONENT_NUMBER": "opponent_number",
    "OPPONENT_HEALTH": "opponent_hp",
    "OPPONENT_HEALTH_MAX": "opponent_hp_max",
    "OPPONENT_STAMINA": "opponent_sp",
    "OPPONENT_STAMINA_MAX": "opponent_sp_max",
    "AFFECTS": "affects",
    "AREA_MAXLEVEL": "area_max_level",
    "AREA_MINLEVEL": "area_min_level",
    "AREA_NAME": "area_name",
    "ROOM_VNUM": "room_vnum",
    "ROOM_EXITS": "room_exits",
    "ROOM_NAME": "room_name",
    "ROOM_TERRAIN": "room_terrain",
    "GOLD": "gold",
    "BANK_GOLD": "bank",
    "EXPERIENCE_MAX": "xp_max",
    "EXPERIENCE_TNL": "xp_tnl",
    "WIMPY": "wimpy",
    "DAMROLL": "damroll",
    "HITROLL": "hitroll",
    "AC": "ac",
    "MOUNT_HEALTH": "mount_hp",
    "MOUNT_HEALTH_MAX": "mount_hp_max",
    "MOUNT_STAMINA": "mount_sp",
    "MOUNT_STAMINA_MAX": "mount_sp_max",
    "MOUNT_NAME": "mount_name",
    "ALIGNMENT": "alignment",
    "STR": "strength",
    "INT": "intelligence",
    "WIS": "wisdom",
    "DEX": "dexterity",
    "CON": "constitution",
    "LUK": "luck",
    "GROUP": "group",
    "UPTIME": "uptime",
    "WORLD_TIME": "world_time",
    "HUNGER": "hunger",
    "THIRST": "thirst",
    "WIELD": "wield",
    "SHIELD": "shield",
    "QUICKDRAW": "quickdraw",
    "HOLD": "hold",
    "HERO_POINTS": "hero",
    "HERO_POINTS_TNL": "hero_tnl",
    "PC_IN_ZONE": "pc_in_area",
    "PC_IN_ROOM": "pc_in_room",
    "PROMPT": "flags"
}

# TODO: disable the abacura @msdp command and let's implement it here
class LOKMSDP(LOKPlugin):

    def __init__(self):
        super().__init__()
        self.msdp_types = {attr_name: type(getattr(self.msdp, attr_name)) for attr_name in MSDP_MAP.values()}

    @command(name="lokmsdp")
    def lok_msdp_command(self, variable: str = '') -> None:
        """Dump MSDP values for debugging"""
        if not self.msdp.reportable_variables:
            self.session.output("[bold red]# MSDPERROR: MSDP NOT LOADED?", markup=True)

        if not variable:
            panel = Panel(Pretty(asdict(self.msdp)), highlight=True)
        else:
            if variable in MSDP_MAP:
                value = getattr(self.msdp, MSDP_MAP[variable])
            else:
                value = getattr(self.msdp, variable)

            panel = Panel(Pretty(value), highlight=True)

        self.session.output(panel, highlight=True, actionable=False)

    @event("msdp_value", priority=1)
    def update_lok_msdp(self, message: MSDPMessage):
        # self.msdp.values[message.type] = message.value

        if message.type in MSDP_MAP:
            attr_name = MSDP_MAP[message.type]
            value = message.value
            if self.msdp_types[attr_name] == int and type(message.value) != int:
                value = 0 if len(message.value) == 0 else int(message.value)

            setattr(self.msdp, attr_name, value)

            # if name == 'MSDP_CHARACTER_NAME':
            #     self.dispatcher.dispatch(event.Event(event.NEW_CHARACTER, value))
