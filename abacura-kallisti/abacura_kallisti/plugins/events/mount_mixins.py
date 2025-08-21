"""
Mount Events Mixin

Contains mount and dismount patterns for the LOK Events system.
This includes mounting and dismounting various creatures.
"""

from abacura.plugins import action
from .messages import MountEvent


class MountEventsMixin:
    """Mixin for mount and dismount event handlers"""
    
    @action(r"^You hop on (.+?)'s back\.")
    def mount_success(self, target: str):
        """Successfully mounted a creature"""
        self.debuglog("info", f"Successfully mounted {target}")
        self.dispatch(MountEvent(target=target, is_mount=True))

    @action(r"^You dismount from (.+?)\.")
    def dismount_success(self, target: str):
        """Successfully dismounted from a creature"""
        self.debuglog("info", f"Successfully dismounted from {target}")
        self.dispatch(MountEvent(target=target, is_mount=False))

    @action(r"^You slide down from (.+?)'s back\.")
    def dismount_slide(self, target: str):
        """Dismounted by sliding down from creature's back"""
        self.debuglog("info", f"Slid down from {target}")
        self.dispatch(MountEvent(target=target, is_mount=False))

    @action(r"^Mount what\?")
    def mount_failure(self):
        """Mount command failed - mount not available"""
        self.debuglog("info", "Mount command failed - mount not available")
        self.dispatch(MountEvent(target="", is_mount=False, is_failure=True))
