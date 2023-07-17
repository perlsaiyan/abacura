import os

from abacura.plugins import ContextProvider
from abacura_kallisti.atlas.world import World
from abacura_kallisti.plugins.msdp import TypedMSDP
from abacura.config import Config
from abacura_kallisti.mud.player import PlayerCharacter
from abacura_kallisti.atlas.location import LocationList
from abacura_kallisti.atlas.room import ScannedRoom


class LOKContextProvider(ContextProvider):
    def __init__(self, config: Config, session_name: str):
        data_dir = config.data_directory(session_name)
        super().__init__(config, session_name)
        self.world: World = World(os.path.join(data_dir, "world.db"))
        self.msdp: TypedMSDP = TypedMSDP()
        self.pc: PlayerCharacter = PlayerCharacter()
        self.locations: LocationList = LocationList(os.path.join(data_dir, "locations.toml"))
        self.room: ScannedRoom = ScannedRoom()

    def get_injections(self) -> dict:
        lok_context = {"world": self.world, "msdp": self.msdp, "pc": self.pc,
                       "locations": self.locations, "room": self.room}

        return lok_context
