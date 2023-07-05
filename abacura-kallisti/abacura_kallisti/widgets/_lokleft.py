"""Legends of Kallisti Left Side Panel Dock"""
from textual import log
from textual.app import ComposeResult
from textual.containers import Container

from abacura.widgets.sidebar import Sidebar
from abacura.widgets.resizehandle import ResizeHandle

from abacura_kallisti.widgets import LOKCharacter, LOKExperience, LOKAffects


class LOKLeft(Sidebar):
    """Left hand dock, intended for user widgets"""
    def compose(self) -> ComposeResult:
        yield ResizeHandle(self, "right")
        with Container(id="leftsidecontainer", classes="SidebarContainer"):
            yield LOKCharacter(id="lok_character")
            yield LOKAffects(id="lok_affects")
            yield LOKExperience(id="lok_experience")
