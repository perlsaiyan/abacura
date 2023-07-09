"""Experimental pixel image widget"""

from rich_pixels import Pixels

from textual.containers import Container, Center, Middle
from textual.widgets import Static

class LOKImage(Static):

    img = None

    def show_image(self, height: int = 0, width: int = 0, image: str = "ship"):
        self.img = Pixels.from_image_path("/home/tom/Pictures/Selection_986.jpg", resize=(width, height * 2))
    
    def render(self):
        if self.img:
            return self.img
        return ""   
