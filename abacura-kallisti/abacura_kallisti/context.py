from abacura.plugins import ContextProvider
from abacura_kallisti.atlas.world import World
from abacura_kallisti.plugins.msdp import TypedMSDP
from abacura_kallisti.plugins.queue import QueueManager
from abacura.config import Config


class LOKContextProvider(ContextProvider):
    def __init__(self, config: Config, session_name: str):
        super().__init__(config, session_name)
        world_filename = config.get_specific_option(session_name, "world_filename")
        self.world: World = World(world_filename)
        self.msdp: TypedMSDP = TypedMSDP()
        self.cq: QueueManager = QueueManager()

    def get_injections(self) -> dict:
        lok_context = {"world": self.world, "msdp": self.msdp, "cq": self.cq}
        return lok_context
