"""Legends of Kallisti Zone information widget"""
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static


from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins.events import event

class LOKZoneHeading(Static):
    z_name: reactive[str | None] = reactive[str | None](None)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.display = False
        self.classes = "WidgetTitle"

    def on_mount(self):
        self.screen.session.listener(self.update_zone_name)

    def render(self) -> str:
        return f"{self.z_name}"

    @event("core.msdp.AREA_NAME")
    def update_zone_name(self, message: MSDPMessage):
        self.z_name = message.value

        if not self.display and self.z_name is not None:
            self.display = True    

class LOKZoneInfo(Static):
    r_name: reactive[str | None] = reactive[str | None](None)
    r_vnum: reactive[str | None] = reactive[str | None](None)
    r_icon: reactive[str] = reactive[str](" ")

    weather_icons = {
        'clear': "[yellow]☀",
        'cloudy': "🌥",
        'snowing': "🌨",
        'sandstorm': "🌪",
        'raining': "🌧",
        'hailing': "⛈",
        'storming': "🌩",
        'maelstrom': "🌀",
        'unknown': " "
    }
    def __init__(self) -> None:
        super().__init__()
        self.display = False
    
    def on_mount(self):
        self.screen.session.listener(self.update_room_name)
        self.screen.session.listener(self.update_room_vnum)
        self.screen.session.listener(self.update_room_weather)


    def render(self) -> str:
        return f"{self.r_icon} {self.r_name} [{self.r_vnum}]"

    @event("core.msdp.ROOM_WEATHER")
    def update_room_weather(self, message: MSDPMessage):
        if message.value in self.weather_icons:
            self.r_icon = self.weather_icons[message.value]
        else:
            self.r_icon = " "

        

    @event("core.msdp.ROOM_VNUM")
    def update_room_vnum(self, message: MSDPMessage):
        self.r_vnum = message.value
        self.display = True

    @event("core.msdp.ROOM_NAME")
    def update_room_name(self, message: MSDPMessage):
        self.r_name = message.value
        self.display = True

class LOKZone(Container):
    """Zone and Room information Widget"""

    def compose(self) -> ComposeResult:
        self.styles.height = 2
        yield LOKZoneHeading()
        yield LOKZoneInfo()

        