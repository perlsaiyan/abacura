import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from itertools import groupby
from pathlib import Path, PurePath
from typing import Tuple, Union, Optional, List

from PIL import Image as PILImageModule
from PIL import ImageSequence
from PIL.Image import Image
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.segment import Segment
from rich.style import Style

from textual.timer import Timer
from textual.widgets import Static

@dataclass
class HalfBlock:
    symbol: str
    fg_color: Optional[Tuple[int, int, int]]
    bg_color: Optional[Tuple[int, int, int]]

    @staticmethod
    @lru_cache(maxsize=1000)
    def get_half_block(top_rgba: Tuple, bottom_rgba: Tuple) -> "HalfBlock":
        top_r, top_g, top_b, top_a = top_rgba
        bot_r, bot_g, bot_b, bot_a = bottom_rgba

        top_color = Color.from_rgb(top_r, top_g, top_b)
        bot_color = Color.from_rgb(bot_r, bot_g, bot_b)

        if top_a != 0 and bot_a != 0:
            return HalfBlock("▀", top_color, bot_color)
        elif top_a == bot_a == 0:
            return HalfBlock(" ", None, None)
        elif top_a == 0:
            return HalfBlock("▄", bot_color, None)
        elif bot_a == 0:
            return HalfBlock("▀", top_color, None)


class RichImage:
    def __init__(self, image: Image, resize: Optional[Tuple[int, int]] = None) -> None:
        self.frames = [frame.copy() for frame in ImageSequence.Iterator(image)]

        if resize:
            [frame.thumbnail(resize, resample=PILImageModule.Resampling.HAMMING) for frame in self.frames]

        self.frames_rgba = [frame.convert("RGBA") for frame in self.frames]
        self.frame_number = 0
        self.frame_loop_number = -1
        self.frame_start_time = datetime.utcnow()
        self.current_frame: Image = self.frames[self.frame_number]

    @staticmethod
    def from_image_path(path: Union[PurePath, str], resize: Optional[Tuple[int, int]] = None) -> "RichImage":
        """Create a RichImage object from an image file.

        Args:
            path: The path to the image file.
            resize: Resize image to (width, height) while preserving aspect ratio
        """

        return RichImage(PILImageModule.open(Path(path)), resize=resize)

    @lru_cache(1000)
    def get_frame_segments(self, frame_number) -> List[Segment]:
        transparent_black = (0, 0, 0, 0)
        segments = []
        strips = []
        rgba_image = self.frames_rgba[self.frame_number]
        width, height = rgba_image.width, rgba_image.height
        #segments.append(Segment(f"Frame: {self.frame_number + 1:03d}/{len(self.frames_rgba):03d} Size: {rgba_image.size}\n",
        #                        Style(color="white", bold=True)))

        for y in range(0, height, 2):
            blocks: List[HalfBlock] = []
            for x in range(width):
                top_pixel = rgba_image.getpixel((x, y))
                if y + 1 < height:
                    bot_pixel = rgba_image.getpixel((x, y + 1))
                else:
                    bot_pixel = transparent_black

                blocks.append(HalfBlock.get_half_block(top_pixel, bot_pixel))

            for block, n in [(block, len(list(g))) for block, g in groupby(blocks)]:
                segments.append(Segment(block.symbol * n, Style(color=block.fg_color, bgcolor=block.bg_color)))

            segments.append(Segment("\n"))

        return segments
        

    def advance_frame(self) -> bool:
        if len(self.frames) == 1:
            return False

        frame_duration = self.current_frame.info.get('duration', 100)
        frame_loops = self.current_frame.info.get("loops", 0)
        if (datetime.utcnow() - self.frame_start_time).total_seconds() * 1000 < frame_duration:
            return False

        self.frame_loop_number += 1

        if self.frame_loop_number < frame_loops:
            return False

        self.frame_loop_number = 0
        self.frame_number = (self.frame_number + 1) % len(self.frames)
        self.current_frame = self.frames[self.frame_number]
        self.frame_start_time = datetime.utcnow()
        return True

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        self.advance_frame()
        segments = self.get_frame_segments(self.frame_number)
        return segments

class LOKGif(Static):

    progress_timer: Timer

    def __init__(self, filename:str, width: int = 0, height: int = 0, **kwargs):
        super().__init__(*kwargs)
        self.filename = filename
        self.image = RichImage.from_image_path(filename, (width, height))
        #self.progress_timer = self.set_interval(1, self.make_progress)
    
    def render(self):
        self.image.advance_frame()
        segments = self.image.get_frame_segments(self.image.frame_number)
        yield(segments)
        

if __name__ == "__main__":
    console = Console()
    images_path = Path("~/Pictures").expanduser()
    # img = RichImage.from_image_path(images_path / "bulbasaur.png", (30, 60))
    # img = RichImage.from_image_path(images_path / "hydra.gif", (40, 40))
    # img = RichImage.from_image_path(images_path / "spaceship.gif", resize=(40, 40))
    img = RichImage.from_image_path(images_path / "edm.gif", (50,50))
    # img = RichImage.from_image_path(images_path / "ship.jpeg", resize=(64, 48))
    # img = RichImage.from_image_path(images_path / "scorpion.png")

    with Live(img, console=console, refresh_per_second=10) as live_console:
        time.sleep(10)

    console.print(HalfBlock.get_half_block.cache_info())
    console.print(img.get_frame_segments.cache_info())
