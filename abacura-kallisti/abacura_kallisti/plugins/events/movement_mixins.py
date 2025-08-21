"""
Movement Events Mixin

Contains all movement and social interaction patterns for the LOK Events system.
This includes arrivals, departures, beckoning, and death events.
"""

from abacura.plugins import action
from .messages import BeckonMessage, ArrivalMessage, DeathMessage, GetItemMessage


class MovementEventsMixin:
    """Mixin for movement and social interaction event handlers"""
    
    # Social interaction patterns
    @action(r"(\w+) beckons you to follow")
    def someone_wants_me(self, leader: str):
        """Someone wants me to follow"""
        self.debuglog("info", f"{leader} beckons me to follow")
        self.dispatch(BeckonMessage(leader=leader))

    @action(r"^(.*) (?:arrives|enters) ?(?:(from the|from|through) (.*)|suddenly)?\.$")
    def someone_arrives(self, name: str, _direction: str, portal: str):
        """Someone arrives"""
        self.debuglog("info", f"{name} arrives from {portal or 'unknown'}")
        arrival_message = ArrivalMessage(name=name, portal=portal or "")
        self.dispatch(arrival_message)

    # Death event
    @action(r"You are dead!  Better luck next time\.\.\.")
    def you_died(self):
        """You died"""
        self.debuglog("info", f"Player died in room {self.msdp.room_vnum}")
        self.dispatch(DeathMessage(room=self.msdp.room_vnum))

    # Item interaction
    @action(r"^You get (.+?)(?: from (.+?))?\.")
    def get_item(self, item: str, container: str):
        """Get an item"""
        get_item_message = GetItemMessage(item=item, container=container, in_inventory=False)

        if container == "None":
            get_item_message.container = ""
        elif container and container.endswith(" in your inventory"):
            get_item_message.container = container.replace(" in your inventory", "")
            get_item_message.in_inventory = True

        self.debuglog(f"Got item: {item} from {container or 'ground'}","info")
        self.dispatch(get_item_message)
