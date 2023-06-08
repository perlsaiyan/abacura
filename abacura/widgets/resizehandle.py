from __future__ import annotations

from rich.segment import Segment

from textual import log, events
from textual.geometry import Offset, Size
from textual.strip import Strip
from textual.widget import Widget



from typing import TYPE_CHECKING, Literal


class ResizeHandle(Widget):
    """A handle for resizing a panel.
    
    This is a child of the panel, and is positioned on the edge of the panel.
    The panel can use min-width, min-height, max-width, and max-height to limit the size.
    """

    DEFAULT_CSS = """
    ResizeHandle {
        width: auto;
        height: auto;
        background: $panel;
        color: rgba(128,128,128,0);
    }
    ResizeHandle:hover {
        background: $panel-lighten-1;
        color: rgba(128,128,128,0.3);
    }
    ResizeHandle.-active {
        background: $panel-darken-1;
    }
    """

    def __init__(
        self,
        target: Widget,
        side: Literal["left", "right", "top", "bottom"],
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._target = target
        self._resizing = False
        self._start_size: Size | None = None
        self._start_mouse_position: Offset | None = None
        self._side: Literal["left", "right", "top", "bottom"] = side
        self._horizontal_resize = side in ("left", "right")
        self.styles.dock = side # type: ignore

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if self.disabled or self._resizing:
            return
        self.capture_mouse()
        self._resizing = True
        self._start_size = self._target.outer_size
        self._start_mouse_position = event.screen_offset
        self.add_class("-active")

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.release_mouse()
        self._resizing = False
        self._start_size = None
        self._start_mouse_position = None
        self.remove_class("-active")

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._resizing:
            return
        assert self._start_size is not None and self._start_mouse_position is not None
        diff = event.screen_offset - self._start_mouse_position
        match self._side:
            case "left":
                self._target.styles.width = self._start_size.width - diff.x
            case "right":
                self._target.styles.width = self._start_size.width + diff.x
            case "top":
                self._target.styles.height = self._start_size.height - diff.y
            case "bottom":
                self._target.styles.height = self._start_size.height + diff.y

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return container.width if not self._horizontal_resize else 1

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return container.height if self._horizontal_resize else 1

    def render_line(self, y: int) -> Strip:
        # char = "⣿" if self._horizontal_resize else "⠶"
        # char = "┃" if self._horizontal_resize else "━"
        # char = "│" if self._horizontal_resize else "─"
        char = "║" if self._horizontal_resize else "═" * self.size.width
        return Strip([Segment(char, self.rich_style)])