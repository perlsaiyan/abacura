import sys
from dataclasses import dataclass
from functools import lru_cache
from itertools import groupby
from typing import Tuple, Optional, List

from PIL import Image as PILImageModule
from PIL import ImageSequence
from PIL.Image import Image
from rich.color import Color
from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.app import App, ComposeResult
from textual.strip import Strip
from textual.widget import Widget


@dataclass
class HalfBlock:
    symbol: str
    fg_color: Optional[Tuple[int, int, int]]
    bg_color: Optional[Tuple[int, int, int]]

    @staticmethod
    @lru_cache(maxsize=1024*16)
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


class ImageWidget(Widget):
    def __init__(self, image_path: str, show_debug: bool=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.image: Image = PILImageModule.open(image_path)
        self.frames: List[Image] = [frame.copy() for frame in ImageSequence.Iterator(self.image)]
        self.strip_cache: List[Optional[List[Strip]]] = [None] * len(self.frames)
        self.frame_number = 0
        self.loop_number = 0
        self.loops = self.image.info.get("loops", 0)
        self.show_debug = show_debug

        self.timer = None

        if len(self.frames) > 1:
            frame_duration = self.frames[self.frame_number].info.get('duration', 100) / 1000
            self.timer = self.set_timer(delay=frame_duration, callback=self.advance_frame)

    async def on_resize(self, e: events.Resize) -> None:
        self.strip_cache = [None] * len(self.frames)

    def advance_frame(self):
        if len(self.frames) <= 1:
            self.refresh()
            return

        self.frame_number = (self.frame_number + 1) % (len(self.frames) - 1)

        if self.frame_number == 0:
            self.loop_number += 1

        if self.loop_number >= self.loops > 0:
            return

        frame_duration = self.frames[self.frame_number].info.get('duration', 100) / 1000
        self.timer = self.set_timer(delay=frame_duration, callback=self.advance_frame)
        self.refresh()

    def get_frame_strips(self, frame_number: int) -> List[Strip]:
        if len(self.strip_cache) == 0:
            return [Strip([])]

        if self.strip_cache[frame_number] is not None:
            return self.strip_cache[frame_number]

        current_frame = self.frames[frame_number].copy()
        w, h = self.size
        current_frame.thumbnail((w, h * 2), resample=PILImageModule.Resampling.NEAREST)

        rgba_image = current_frame.convert("RGBA")
        width, height = rgba_image.width, rgba_image.height

        strips: List[Strip] = []
        for y in range(0, height, 2):
            blocks: List[HalfBlock] = []
            for x in range(width):
                top_pixel = rgba_image.getpixel((x, y))
                if y + 1 < height:
                    bot_pixel = rgba_image.getpixel((x, y + 1))
                else:
                    bot_pixel = (0, 0, 0, 0)

                blocks.append(HalfBlock.get_half_block(top_pixel, bot_pixel))

            segments = []
            for block, n in [(block, len(list(g))) for block, g in groupby(blocks)]:
                segments.append(Segment(block.symbol * n, Style(color=block.fg_color, bgcolor=block.bg_color)))

            strips.append(Strip(segments))

        self.strip_cache[frame_number] = strips
        return strips

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""

        if len(self.frames) == 0:
            return Strip([])

        strips = self.get_frame_strips(self.frame_number)

        if self.show_debug and y == 0:
            # show info in the first line
            frame_duration = self.frames[self.frame_number].info.get('duration', 100) / 1000
            header_text = f"Fr: {self.frame_number + 1:03d}/{len(self.frames):03d} "
            header_text += f"({self.size.width}x{self.size.height}) [{frame_duration:2.2}s]"
            header_text += " " * 400

            return Strip([Segment(header_text[:self.size.width], Style(color="white", bold=True))])

        if y < len(strips):
            return strips[y]

        return Strip([])


class ImageApp(App):
    """A simple app to show our widget."""

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def compose(self) -> ComposeResult:
        yield ImageWidget(self.image_path, show_debug=True)


if __name__ == "__main__":
    # from abacura.utils import profiler
    # profiler.profile_on()
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
        print(image_file)
        app = ImageApp(image_file)
        app.run()
    else:
        print("Please specify image to load")

    # profiler.profile_off()
    # stats_dict = profiler.get_profile_stats()
    #
    # from rich.table import Table
    # tbl = Table()
    # tbl.add_column("Function")
    # tbl.add_column("Calls")
    # tbl.add_column("Elapsed")
    # tbl.add_column("CPU")
    # tbl.add_column("Self Time")
    # for pfn in sorted(stats_dict.values(), key=lambda x: x.self_time, reverse=True)[:50]:
    #     tbl.add_row(pfn.function.get_location(), str(pfn.call_count),
    #                 format(pfn.elapsed_time, "6.3f"), format(pfn.cpu_time, "6.3f"),
    #                 format(pfn.self_time, '6.3f'))
    # from rich.console import Console
    # console = Console()
    # console.print(tbl)
