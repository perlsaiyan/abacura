"""DOM inspector development tool for Textual."""

__all__ = ["Inspector"]

__author__ = "Isaiah Odhner"
__email__ = "isaiahodhner@gmail.com"
__version__ = "0.0.0"
__license__ = "MIT"
"""
Copyright (c) 2023 Isaiah Odhner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import inspect
import os
from typing import Any, Iterable, NamedTuple, Optional, Type, TypeGuard

from rich.markup import escape
from rich.style import Style
from rich.text import Text
from rich.highlighter import ReprHighlighter
# from rich.syntax import Syntax
from textual import events
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Container, VerticalScroll
from textual.css.match import match
from textual.css.model import RuleSet
from textual.css.styles import RulesMap, Styles
from textual.dom import DOMNode
from textual.errors import NoWidget
from textual.geometry import Offset, Region
from textual.message import Message
from textual.reactive import var

from textual.widget import Widget
from textual.widgets import Button, Static, TabPane, TabbedContent, Tree
from textual.widgets.tree import TreeNode
# from textual.css._style_properties import BorderDefinition

from abacura.widgets.resizehandle import ResizeHandle
#from launch_editor import launch_editor

# Instrument style setting in order to link to the source code where inline styles are set.
inline_style_call_stacks: dict[DOMNode, dict[str, list[inspect.FrameInfo]]] = {}
original_set_rule = Styles.set_rule
def set_rule(self: Styles, rule: str, value: object | None) -> bool:
    if self.node and self.node.styles.inline is self:
        if self.node not in inline_style_call_stacks:
            inline_style_call_stacks[self.node] = {}
        inline_style_call_stacks[self.node][rule] = inspect.stack()
    return original_set_rule.__get__(self)(rule, value)
Styles.set_rule = set_rule

rule_set_call_stacks: dict[RuleSet, list[inspect.FrameInfo]] = {}
original_rule_set_init = RuleSet.__init__
def rule_set_init(self: RuleSet, *args, **kwargs):
    original_rule_set_init.__get__(self)(*args, **kwargs)
    rule_set_call_stacks[self] = inspect.stack()
RuleSet.__init__ = rule_set_init


def subtract_regions(a: Region, b: Region) -> list[Region]:
    """Subtract region `b` from region `a`."""
    result: list[Region] = []

    # Check for no overlap or complete containment
    if (
        b.x >= a.x + a.width or
        b.x + b.width <= a.x or
        b.y >= a.y + a.height or
        b.y + b.height <= a.y
    ):
        result.append(a)
        return result

    # Check for complete overlap
    if (
        b.x >= a.x and
        b.x + b.width <= a.x + a.width and
        b.y >= a.y and
        b.y + b.height <= a.y + a.height
    ):
        return result

    # Calculate remaining regions
    if b.x > a.x:
        result.append(Region(a.x, a.y, b.x - a.x, a.height))
    if b.x + b.width < a.x + a.width:
        result.append(Region(b.x + b.width, a.y, a.x + a.width - (b.x + b.width), a.height))
    if b.y > a.y:
        result.append(Region(a.x, a.y, a.width, b.y - a.y))
    if b.y + b.height < a.y + a.height:
        result.append(Region(a.x, b.y + b.height, a.width, a.y + a.height - (b.y + b.height)))

    return result

def subtract_multiple_regions(base: Region, negations: Iterable[Region]) -> list[Region]:
    """Subtract multiple regions from a base region."""
    result: list[Region] = [base]
    for negation in negations:
        new_result: list[Region] = []
        for region in result:
            new_result.extend(subtract_regions(region, negation))
        result = new_result
    return result

class DOMTree(Tree[DOMNode]):
    """A widget that displays the widget hierarchy."""
    
    class Hovered(Message, bubble=True):
        """Posted when a node in the tree is hovered with the mouse or highlighted with the keyboard.

        Handled by defining a `on_domtree_hovered` method on a parent widget.
        """

        def __init__(
            self, tree: "DOMTree", tree_node: TreeNode[DOMNode] | None, dom_node: DOMNode | None
        ) -> None:
            """Initialise the Hovered message.

            Args:
                tree: The `DOMTree` that had a node hovered.
                tree_node: The tree node for the file that was hovered.
                dom_node: The DOM node that was hovered.
            """
            super().__init__()
            self.tree: DOMTree = tree
            """The `DOMTree` that had a node hovered."""
            self.tree_node: TreeNode[DOMNode] | None = tree_node
            """The tree node that was hovered. Only _represents_ the DOM node."""
            self.dom_node: DOMNode | None = dom_node
            """The DOM node that was hovered."""

        # @property
        # def control(self) -> "DOMTree":
        #     """The `DOMTree` that had a node hovered.

        #     This is an alias for [`Hovered.tree`][textual_paint.inspector.DOMTree.Hovered.tree]
        #     which is used by the [`on`][textual.on] decorator.
        #     """
        #     return self.tree

    class Selected(Message, bubble=True):
        """Posted when a node in the tree is selected.

        Handled by defining a `on_domtree_selected` method on a parent widget.
        """

        def __init__(
            self, tree: "DOMTree", tree_node: TreeNode[DOMNode], dom_node: DOMNode
        ) -> None:
            """Initialise the Selected message.

            Args:
                tree: The `DOMTree` that had a node selected.
                tree_node: The tree node for the file that was selected.
                dom_node: The DOM node that was selected.
            """
            super().__init__()
            self.tree: DOMTree = tree
            """The `DOMTree` that had a node selected."""
            self.tree_node: TreeNode[DOMNode] = tree_node
            """The tree node that was selected. Only _represents_ the DOM node."""
            self.dom_node: DOMNode = dom_node
            """The DOM node that was selected."""

    def __init__(
        self,
        root: DOMNode,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        """Initialise the DOMTree widget."""
        super().__init__(
            root.css_identifier_styled,
            root,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def _on_tree_node_expanded(self, event: Tree.NodeExpanded[DOMNode]) -> None:
        """Called when a node is expanded; loads the children."""
        event.stop()
        dom_node = event.node.data
        if dom_node is None:
            return
        # event.node.remove_children() was inefficient and maybe caused some other problems
        for child in dom_node.children:
            exists = False
            for node in event.node.children:
                if node.data == child:
                    exists = True
                    break
            if exists:
                continue
            event.node.add(
                child.css_identifier_styled,
                data=child,
                allow_expand=len(child.children) > 0,
            )

    def _on_tree_node_highlighted(self, event: Tree.NodeHighlighted[DOMNode]) -> None:
        """Called when a node is highlighted with the keyboard."""
        event.stop()
        dom_node = event.node.data
        if dom_node is None:
            return
        self.post_message(self.Hovered(self, event.node, dom_node))

    def _on_tree_node_selected(self, event: Tree.NodeSelected[DOMNode]) -> None:
        """Called when a node is selected with the mouse or keyboard."""
        event.stop()
        dom_node = event.node.data
        if dom_node is None:
            return
        self.post_message(self.Selected(self, event.node, dom_node))

    def watch_hover_line(self, previous_hover_line: int, hover_line: int) -> None:
        """Extend the hover line watcher to post a message when a node is hovered."""
        # Could use self.watch() instead https://textual.textualize.io/api/dom_node/#textual.dom.DOMNode.watch
        super().watch_hover_line(previous_hover_line, hover_line)
        node: TreeNode[DOMNode] | None = self._get_node(hover_line) if hover_line > -1 else None
        # print("watch_hover_line", previous_hover_line, hover_line, node)
        if node is not None:
            assert isinstance(node.data, DOMNode), "All nodes in DOMTree should have DOMNode data, got: " + repr(node.data)
            self.post_message(self.Hovered(self, node, node.data))
        else:
            self.post_message(self.Hovered(self, None, None))
    
    def on_leave(self, event: events.Leave) -> None:
        """Handle the mouse leaving the tree."""
        self.hover_line = -1

    async def expand_to_dom_node(self, dom_node: DOMNode) -> None:
        """Drill down to the given DOM node in the tree."""
        tree_node = self.root
        # Expand nodes until we get to the one we want.
        for dom_node in reversed(dom_node.ancestors_with_self):
            for node in (*tree_node.children, tree_node): # tree_node in case it's the root
                if node.data == dom_node:
                    tree_node = node
                    tree_node.expand()
                    async def wait_for_expand() -> None:
                        # while not tree_node.is_expanded: # this is set immediately
                        #     await asyncio.sleep(0.01)
                        await asyncio.sleep(0.01)
                    task = asyncio.create_task(wait_for_expand())
                    self._wait_for_expand = task
                    await task
                    del self._wait_for_expand
                    break
        # Select the node in the tree.
        # Note: `select_node` just places the cursor on the node. It doesn't actually select it.
        self.select_node(tree_node)
        self.scroll_to_node(tree_node)
        # Don't toggle the node when selecting it.
        auto_expand = self.auto_expand
        self.auto_expand = False
        self.action_select_cursor()
        self.auto_expand = auto_expand


class _ShowMoreSentinelType: pass
_ShowMoreSentinel = _ShowMoreSentinelType()
"""A sentinel that represents an ellipsis that can be clicked to load more properties."""
del _ShowMoreSentinelType

class PropertiesTree(Tree[object]):
    """A widget for exploring the attributes/properties of an object."""

    highlighter = ReprHighlighter()

    def __init__(
        self,
        label: str,
        root: object = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        """Initialise the PropertiesTree widget."""
        super().__init__(
            label,
            root,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

        self._already_loaded: dict[TreeNode[object], set[str]] = {}
        """A mapping of tree nodes to the keys that have already been loaded.
        
        This allows the tree to be collapsed and expanded without duplicating nodes.
        It's also used for lazy-loading nodes when clicking the ellipsis in long lists...
        """

        self._num_keys_accessed: dict[TreeNode[object], int] = {}
        """A mapping of tree nodes to the number of keys that have been accessed."""

    def _on_tree_node_expanded(self, event: Tree.NodeExpanded[object]) -> None:
        """Called when a node is expanded; loads the children."""
        event.stop()
        self._populate_node(event.node)

    def _on_tree_node_selected(self, event: Tree.NodeSelected[object]) -> None:
        """Called when a node is selected with the mouse or keyboard."""
        event.stop()
        if event.node.data is _ShowMoreSentinel:
            event.node.remove()
            assert event.node.parent is not None, "Show more node should have a parent"
            self._populate_node(event.node.parent, load_more=True)

    @property
    def AAA_deal_with_it(self) -> dict[str, Any]:
        """This property gives a grab bag of different types to test the tree."""
        from enum import Enum
        from typing import NamedTuple
        import traceback
        return {
            "a_string": "DEAL WITH IT 😎",
            "an_int": 42,
            "a_float": 3.14,
            "a_bool": True,
            "none": None,
            "a_list": ["a", "b", "c"],
            "a_tuple": ("a", "b", "c"),
            "a_named_tuple": NamedTuple("a_named_tuple", [("a", int), ("b", str), ("c", float)])(1, "2", 3.0),
            "a_set": {"a", "b", "c"},
            "a_frozenset": frozenset({"a", "b", "c"}),
            "a_dict": {"a": "A", "b": "B", "c": "C"},
            "a_dict_with_mixed_keys": {1: "A", "b": "B", Enum("an_enum", "a b c"): "C", frozenset(): "D"},
            "a_parameterized_generic": dict[str, int],
            "a_module": inspect,
            "a_function": lambda x: x,  # type: ignore
            "a_generator": (x for x in "abc"),
            "an_iterator": iter("abc"),
            "a_range": range(10),
            "a_slice": slice(1, 2, 3),
            "a_complex": 1 + 2j,
            "a_bytes": b"abc",
            "a_bytearray": bytearray(b"abc"),
            "an_enum": Enum("an_enum", "a b c"),
            "an_ellipsis": ...,
            "a_memoryview": memoryview(b"abc"),
            "not_implemented": NotImplemented,
            "an_exception": Exception("hello"),
            "a_type": type,
            "a_code": compile("print('hello')", "<string>", "exec"),
            "a_frame": inspect.currentframe(),
            "a_traceback": traceback.extract_stack(),
        }
    
    @property
    def AAA_test_property_that_raises_exception(self) -> str:
        """This property raises an exception when accessed.
        
        Navigate to this node in the DOM Tree and look in the Properties Panel to see the error message.
        """
        raise Exception("EMIT: Error Message Itself Test")

    def filter_property(self, key: str, value: object) -> bool:
        """Return True if the property should be shown in the tree."""
        # TODO: allow toggling filtering of private properties
        # (or show in a collapsed node)
        return not key.startswith("_") and not callable(value)

    def _populate_node(self, node: TreeNode[object], load_more: bool = False) -> None:
        """Populate a node with its children, or some of them.
        
        If load_more is True (ellipsis node clicked), load more children.
        Otherwise just load an initial batch.
        If the node is collapsed and re-expanded, no new nodes should be added.
        """
        data: object = node.data
        if data is None:
            return

        if node not in self._already_loaded:
            self._already_loaded[node] = set()
            self._num_keys_accessed[node] = 0

        max_keys = 100 # Max keys to load at once; may add less nodes due to filtering
        if load_more:
            max_keys += self._num_keys_accessed[node]

        count = 0
        """Key index + 1, including filtered-out keys."""

        ellipsis_node: TreeNode[object] | None = None
        """Node to show more properties when clicked."""
        
        only_counting = False
        """Flag set when we've reached the limit and aren't adding any more nodes."""

        def safe_dir_items(obj: object) -> Iterable[tuple[str, object, Exception | None]]:
            """Yields tuples of (key, value, error) for each key in dir(obj)."""
            # for key, value in obj.__dict__.items():
            # inspect.getmembers is better than __dict__ because it includes getters
            # except it can raise errors from any of the getters, and I need more granularity
            # for key, value in inspect.getmembers(obj):
            # TODO: handle DynamicClassAttributes like inspect.getmembers does
            for key in dir(obj):
                if only_counting:
                    # Optimization: don't call getattr(); otherwise it would partially defeat the purpose of eliding nodes
                    yield (key, None, None)
                    continue
                try:
                    yield (key, getattr(obj, key), None)
                except Exception as e:
                    yield (key, None, e)

        def with_no_error(key_val: tuple[str, object]) -> tuple[str, object, None]:
            """Adds a None error slot to a key-value pair."""
            return (key_val[0], key_val[1], None)

        iterator: Iterable[tuple[str, object, Exception | None]]

        # Dictionaries are iterable, but we want key-value pairs, not index-key pairs
        if isinstance(data, dict):
            iterator = map(with_no_error, data.items())  # type: ignore
        # Prefer dir() for NamedTuple, but enumerate() for lists (and tentatively all other iterables)
        elif isinstance(data, Iterable) and not hasattr(data, "_fields"):  # type: ignore
            iterator = map(with_no_error, enumerate(data))  # type: ignore
        else:
            iterator = safe_dir_items(data)  # type: ignore
        
        self._num_keys_accessed[node] = 0
        for key, value, exception in iterator:
            count += 1
            if only_counting:
                continue
            self._num_keys_accessed[node] += 1
            if not self.filter_property(str(key), value):
                continue
            if str(key) in self._already_loaded[node]:
                continue
            if count > max_keys:
                for child in node.children:
                    if child.data is _ShowMoreSentinel:
                        child.remove()
                ellipsis_node = node.add("...", _ShowMoreSentinel)
                ellipsis_node.allow_expand = False
                # break
                only_counting = True
                continue
            PropertiesTree._add_property_node(node, str(key), value, exception)
            self._already_loaded[node].add(str(key))
        if ellipsis_node is not None:
            ellipsis_node.label = f"... +{count - max_keys} more"

    @classmethod
    def _add_property_node(cls, parent_node: TreeNode[object], name: str, data: object, exception: Exception | None = None) -> None:
        """Adds data to a node.

        Based on https://github.com/Textualize/textual/blob/65b0c34f2ed6a69795946a0735a51a463602545c/examples/json_tree.py

        Args:
            parent_node (TreeNode): A Tree node to add a child to.
            name (str): The key that the data is associated with.
            data (object): Any object ideally should work.
        """

        node = parent_node.add(name, data)

        def with_name(text: Text) -> Text:
            """Formats a key=value line."""
            return Text.assemble(
                Text.styled(name, "bold"), "=", text
            )

        if exception is not None:
            node.allow_expand = False
            node.set_label(with_name(Text.from_markup(f"[i][#808080](getter error: [red]{escape(repr(exception))}[/red])[/#808080][/i]")))
        elif isinstance(data, (list, set, frozenset, tuple)):
            length = len(data)  # type: ignore
            # node.set_label(Text(f"{name} ({length})"))
            # node.set_label(with_name(PropertiesTree.highlighter(repr(data))))
            # node.set_label(Text.assemble(
            #     Text.from_markup(f"[#808080]({length})[/#808080] "),
            #     with_name(PropertiesTree.highlighter(repr(data))),
            # ))
            # node.set_label(Text.assemble(
            #     with_name(PropertiesTree.highlighter(repr(data))),
            #     Text.from_markup(f" [#808080]({length})[/#808080]"),
            # ))
            # In the middle I think is best, although it's a little more complex:
            node.set_label(Text.assemble(
                Text.styled(name, "bold"),
                Text.styled(f"({length})", "#808080"),
                "=",
                PropertiesTree.highlighter(repr(data))  # type: ignore
            ))
            # Can I perhaps DRY with with_name() with with_name taking a length parameter? In other words:
            # Can I maybe DRY this with with_name with with_name with with_name(text, length) as the signature?
        elif isinstance(data, (str, bytes, int, float, bool, type(None))):
            node.allow_expand = False
            node.set_label(with_name(PropertiesTree.highlighter(repr(data))))
        elif callable(data):
            # Filtered out by default
            # TODO: allow expanding things like widget.log, which is callable but also has methods for each log type
            node.allow_expand = False
            node.set_label(Text.assemble(
                f"{type(data).__name__} ",
                Text.styled(name, "bold"),
                PropertiesTree.highlighter(str(inspect.signature(data))),
            ))
        elif hasattr(data, "__dict__") or hasattr(data, "__slots__") or isinstance(data, dict):
            # Pyright gives an error here due to the more specific "object | dict[Unknown, Unknown]"
            # even though object is a superclass of dict and repr takes an object.
            node.set_label(with_name(PropertiesTree.highlighter(repr(data))))  # type: ignore
        else:
            node.allow_expand = False
            node.set_label(with_name(PropertiesTree.highlighter(repr(data))))



class NodeInfo(Container):

    class FollowLinkToNode(Message):
        """A message sent when a link is clicked, pointing to a DOM node."""
        def __init__(self, dom_node: DOMNode) -> None:
            super().__init__()
            self.dom_node = dom_node

    class StaticWithLinkSupport(Static):
        """Static text that supports DOM node links and file opening links.
        
        This class exists because actions can't target an arbitrary parent.
        The only supported namespaces are `screen` and `app`.
        So action_select_node has to be defined directly on the widget that
        contains the @click actions.
        (Maybe it could be an ad-hoc method on the widget instead.)
        https://textual.textualize.io/guide/actions/#namespaces
        """

        def __init__(self, node_info: "NodeInfo", *, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
            super().__init__(name=name, id=id, classes=classes, disabled=disabled)
            self._node_info = node_info

        def action_select_node(self, link_id: int) -> None:
            """Select a DOM node."""
            dom_node = self._node_info._link_id_to_node.get(link_id)
            print("action_select_node", link_id, dom_node)
            if dom_node is None:
                return
            self.post_message(NodeInfo.FollowLinkToNode(dom_node))
        
        def action_open_file(self, path: str, line_number: int | None = None, column_number: int | None = None) -> None:
            """Open a file."""
            print("action_open_file", path, line_number, column_number)
            #launch_editor(path, line_number, column_number)


    dom_node: var[DOMNode | None] = var[Optional[DOMNode]](None)
    """The DOM node being inspected."""

    def __init__(self, *, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        self._link_id_counter = 0
        """A counter used to generate unique IDs for links,
        since CSS selectors aren't unique (without something like `nth-child()`),
        and DOMNodes can't be used as arguments to an action function.
        """

        self._link_id_to_node: dict[int, DOMNode] = {}
        """A mapping of link IDs to DOM nodes."""

    def compose(self) -> ComposeResult:
        """Add sub-widgets."""
        # FIXME: when resizing NodeInfo very large, the scrollbar stops reaching all the way, and eventually disappears.
        # I think NodeInfo is going offscreen in this case, since it's not limited by what the layout can fit.
        yield ResizeHandle(self, "top")
        with TabbedContent(initial="properties"):
            with TabPane("Props", id="properties"):
                yield PropertiesTree("", classes="properties")
                yield Static("", classes="properties_nothing_selected tab_content_static")
            with TabPane("CSS", id="styles"):
                yield VerticalScroll(self.StaticWithLinkSupport(self, classes="styles tab_content_static"))
            with TabPane("Keys", id="key_bindings"):
                yield VerticalScroll(Static(classes="key_bindings tab_content_static"))
            with TabPane("Events", id="events"):
                yield VerticalScroll(self.StaticWithLinkSupport(self, classes="events tab_content_static"))

    def watch_dom_node(self, dom_node: DOMNode | None) -> None:
        """Update the info displayed when the DOM node changes."""
        print("watch_dom_node", dom_node)

        self._link_id_to_node.clear()

        properties_tree = self.query_one(PropertiesTree)
        properties_static = self.query_one(".properties_nothing_selected", Static)
        styles_static = self.query_one(".styles", Static)
        key_bindings_static = self.query_one(".key_bindings", Static)
        events_static = self.query_one(".events", Static)

        if dom_node is None:
            nothing_selected_message = "Nothing selected"
            properties_tree.display = False
            properties_static.display = True
            properties_tree.reset("", None)
            properties_static.update(nothing_selected_message)
            styles_static.update(nothing_selected_message)
            key_bindings_static.update(nothing_selected_message)
            events_static.update(nothing_selected_message)
            return

        properties_tree.display = True
        properties_static.display = False
        properties_tree.reset(dom_node.css_identifier_styled, dom_node)
        # trigger _on_tree_node_expanded to load the first level of properties
        properties_tree.root.collapse()
        properties_tree.root.expand()

        highlighter = ReprHighlighter()

        # styles_static.update(dom_node.styles.css)
        # styles_static.update(Syntax(f"all styles {{\n{dom_node.styles.css}\n}}", "css"))
        # TODO: sort by specificity
        # TODO: syntax highlight (`Syntax(css, "css")` almost works but is ugly/inconsistent because it assumes Web CSS flavor, not Textual CSS.)
        # TODO: mark styles that don't apply because they're overridden
        # TODO: edit/toggle rules

        stylesheet = dom_node.app.stylesheet # type: ignore
        rule_sets = stylesheet.rules
        applicable_rule_sets: list[RuleSet] = []
        for rule_set in rule_sets:
            selector_set = rule_set.selector_set
            if match(selector_set, dom_node):
                applicable_rule_sets.append(rule_set)
        
        to_ignore = [
            ("inspector.py", "set_rule"), # inspector's instrumentation
            ("styles.py", "set_rule"),
            ("_style_properties.py", "__set__"),
            # framework style setter shortcuts
            # found with regexp /self\.styles\.(\w+) = /
            ("dom.py", "display"),
            ("dom.py", "visible"),
            ("widget.py", "offset"),
        ]
        def should_ignore(frame_info: inspect.FrameInfo) -> bool:
            """Filter out frames that are not relevant to the user."""
            for (ignore_filename, ignore_func_name) in to_ignore:
                if frame_info.filename.endswith(ignore_filename) and frame_info.function == ignore_func_name:
                    return True
            return False
        def trace_inline_style(rule: str) -> tuple[str, int] | None:
            """Returns the location where a style is set, or None if it can't be found."""
            try:
                source = inline_style_call_stacks[dom_node]
                # This can definitely cause KeyError, though I'm not quite sure why yet
                # maybe styles are set other than through `set_rule`,
                # such as `merge` or `merge_rules`?
                # Or it could have to do with compound properties since `border` is a shorthand,
                # and it's the one that's causing the KeyError. That's probably it. TODO: try to fix this.
                frame_infos = source[rule]
            except KeyError:
                return None
            frame_infos = [frame_info for frame_info in frame_infos if not should_ignore(frame_info)]
            if not frame_infos:
                return None
            try:
                # The first frame after the ignored ones is likely the one we want.
                # However, if you define a helper function for setting styles,
                # it may not be very useful, as it would only locate the helper function.
                # The UI is only a single button, for now, but full stack traces could be exposed.
                frame_info = frame_infos[0]
            except IndexError: # just in case
                return None
            return (frame_info.filename, frame_info.lineno)
        
        def format_location_info(location: tuple[str, int | None] | None) -> Text:
            """Shows a link to open the the source code where a style is set."""
            if location is None:
                return Text.styled(f"(unknown location)", "#808080")
            else:
                file, line_number = location
                action = f"open_file({file!r}, {line_number!r})"
                file_name = os.path.basename(file)
                location_string = f"{file_name}:{line_number}" if line_number is not None else file_name
                return Text.styled(location_string, Style(meta={"@click": action}))

        # `css_lines` property has the code for formatting declarations;
        # I don't think there's a way to do it for a single declaration.
        # css_lines = dom_node.styles.inline.css_lines
        # But we need to associate the snake_cased/hyphenated/shorthand CSS property names,
        # in order to provide links to the source code.
        inline_styles = dom_node.styles.inline
        inline_rules = inline_styles.get_rules()
        def format_inline_style_line(rule: str) -> Text:
            """Formats a single CSS line for display, with a link to open the source code."""
            # Ugly hack for creating a string from a single rule,
            # while associating the snake_cased/hyphenated/shorthand CSS property names.
            # TODO: display as shorthand properties when possible, as css_lines does.
            # This code currently breaks things up into the individual rules,
            # in order to associate the stack traces with the rules.
            # (The stacks are captured for individual properties, not shorthands.)
            # This could be cleaned up a lot with some API changes in `Styles`.
            single_rule_rules_map = RulesMap()
            single_rule_rules_map[rule] = inline_rules[rule]
            important: set[str] = set()
            if rule in inline_styles.important:
                important.add(rule)
            single_rule_styles = Styles(
                node=inline_styles.node,
                _rules=single_rule_rules_map,
                important=important
            )

            css_line = single_rule_styles.css_lines[0]
            rule_hyphenated, value = css_line.split(":", 1)
            rule_hyphenated = rule_hyphenated.strip()
            value = value.strip()
            return Text.assemble(
                "  ",
                rule_hyphenated,
                ": ",
                value,
                " ",
                format_location_info(trace_inline_style(rule)),
            )
        inline_style_text = Text.assemble(
            Text.styled("inline styles", "italic"),
            " {\n",
            Text("\n").join(
                format_inline_style_line(rule) for rule in inline_rules
            ),
            "\n}",
        )

        def format_rule_set(rule_set: RuleSet) -> Text:
            """Formats a CSS rule set for display, with a link to open the source code."""
            path: str | None = None
            line_number: int | None = None
            try:
                stack = rule_set_call_stacks[rule_set]
                # look up the stack to find local named "path"
                for frame_info in stack:
                    if frame_info.function == "parse":
                        path = frame_info.frame.f_locals["path"]
                        assert isinstance(path, str)
                        break
            except KeyError:
                path = None
                pass
            if path is not None and ":" in path:
                path, widget_name = path.rsplit(":", 1)
                # parse the python file to find the line number of the widget definition
                # could use `ast` module for robustness
                # to avoid things like finding DEFAULT_CSS from the wrong widget
                with open(path) as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if f"class {widget_name}" in line:
                        line_number = i + 1
                        # keep looking for DEFAULT_CSS more specifically
                    if line_number is not None and "DEFAULT_CSS" in line:
                        line_number = i + 1
                        # TODO: find the specific line number of the rule set
                        break
            css = rule_set.css
            selectors, declarations_and_end_curly = css.split("{", 1)
            return Text.assemble(
                selectors,
                "{ ",
                format_location_info((path, line_number) if path else None),
                declarations_and_end_curly,
            )

        styles_text = Text.assemble(
            inline_style_text,
            "\n\n",
            Text("\n\n").join(format_rule_set(rule_set) for rule_set in applicable_rule_sets),
        )
        styles_static.update(styles_text)

        # key_bindings_static.update("\n".join(map(repr, dom_node.BINDINGS)) or "(None defined with BINDINGS)")
        key_bindings_static.update(Text("\n").join(map(lambda binding: highlighter(repr(binding)), dom_node.BINDINGS)) or "(None defined with BINDINGS)")

        # For events, look for class properties that are subclasses of Message
        # to determine what events are available.
        # TODO: also include built-in events not defined on a widget class
        # Also, there's plenty of UI work to do here.
        # Should it separate posted vs handled events?
        # Documentation strings could go in tooltips or otherwise be abbreviated.
        # Source code links could go in tooltips, which might help to prevent line-
        # breaks, which break automatic <file>:<line> linking (Ctrl+Click support) in VS Code.
        available_events: list[Type[Message]] = []
        for cls in type(dom_node).__mro__:
            for value in cls.__dict__.values():
                if isinstance(value, type) and issubclass(value, Message):
                    available_events.append(value)

        def format_object_location_info(obj: Any) -> Text:
            """Shows the source code location of an object, with a link to open the file."""
            try:
                line_number = inspect.getsourcelines(obj)[1]
                file = inspect.getsourcefile(obj)
                return format_location_info((file, line_number) if file else None)
            except OSError as e:
                return Text.from_markup(f"[#808080](error getting location: [red]{escape(repr(e))}[/red])[/#808080]")

        def message_info(message_class: Type[Message]) -> Text:
            """Return a description of a message class, listing any handlers."""
            handler_name = message_class.handler_name
            handler_names = [handler_name, f"_{handler_name}"]
            # Find any listeners for this event
            # Only look upwards if the event bubbles
            potential_handlers = dom_node.ancestors_with_self if message_class.bubble else [dom_node]
            usages: list[Text] = []
            for ancestor in potential_handlers:
                for handler_name in handler_names:
                    if hasattr(ancestor, handler_name):
                        # Record which class the handler is defined on
                        # Not sure which order would be needed here
                        # for cls in type(ancestor).__mro__:
                        #     if hasattr(cls, handler_name):
                        #         ...
                        #         break
                        # But there's a simpler way: method.__self__.__class__
                        handler = getattr(ancestor, handler_name)
                        defining_class = handler.__self__.__class__
                        def_location = format_object_location_info(handler)
                        # Note: css_path_nodes is just like ancestors_with_self, but reversed; it's still DOM nodes
                        descendant_arrow = Text.styled(" > ", "#808080")
                        dom_path = descendant_arrow.join([css_path_node.css_identifier_styled for css_path_node in ancestor.css_path_nodes])
                        link_id = self._link_id_counter
                        self._link_id_counter += 1
                        self._link_id_to_node[link_id] = ancestor
                        dom_path.apply_meta({"@click": f"select_node({link_id})"})
                        handler_qualname = f"{defining_class.__qualname__}.{handler_name}"
                        usages.append(Text.assemble(
                            # "Listener on DOM node: ", # too verbose
                            "🎯 ", # looks nice; different metaphor
                            # "📥 ", fits mail metaphor
                            # "📭 ", fits mail metaphor
                            # Fitting the mail metaphor is not necessarily the best way to go since
                            # a Message class delivered like a letter is. It bubbles up the DOM tree. 🫧🆙🌲
                            dom_path,
                            "\n\n",
                            handler_qualname,
                            " ",
                            def_location,
                        ))
            if usages:
                usage_info = Text("\n\n").join(usages)
            else:
                usage_info = Text(f"No listeners found for {' or '.join(handler_names)}")
            
            def_location = format_object_location_info(message_class)
            qualname = message_class.__qualname__
            doc = inspect.getdoc(message_class) or '(No docstring)'
            return Text.assemble(
                # ✉️ doesn't show up as an emoji in VS Code at least
                # 📨 shows with an inbox tray in Apple's emoji font
                # "📩 ", is okay
                # "📤 ", is too similar to 📥 for visual scanning
                "📧 ", # represents email, but the E could be said to stand for "Event"
                Text.styled(qualname, "bold"),
                " ",
                def_location,
                "\n",
                Text.styled(doc, "#808080"),
                "\n",
                usage_info,
                "\n",
            )

        if available_events:
            events_static.update(Text("\n").join(map(message_info, available_events)))
        else:
            events_static.update(f"(No message types exported by {type(dom_node).__name__!r} or its superclasses)")



class OriginalStyles(NamedTuple):
    """The original styles of a widget before highlighting."""

    # border: BorderDefinition | None
    # """The original border of the widget."""
    # border_title: str | Text | None
    # """The original border title of the widget."""
    # background: Color | None
    # """The original background of the widget."""
    tint: Color | None
    """The original tint of the widget."""

ALLOW_INSPECTING_INSPECTOR = True
"""Whether widgets in the inspector can be picked for inspection."""

class Inspector(Container):
    """UI for inspecting the layout of the application."""

    DEFAULT_CSS = """
    Inspector {
        dock: right;
        width: 40;
        min-width: 15;
        border-left: wide $panel-darken-2;
        background: $panel;
    }
    Inspector Button.inspect_button {
        margin: 1;
        width: 1fr;
    }
    Inspector Button.inspect_button.picking {
        color: $accent;
    }
    Inspector DOMTree {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    Inspector NodeInfo,
    Inspector TabbedContent,
    Inspector ContentSwitcher,
    Inspector TabPane,
    Inspector TabPane > VerticalScroll {
        width: 1fr !important;
        height: 1fr !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    Inspector .tab_content_static {
        margin-bottom: 1;
        link-color: $accent;
    }
    """

    picking = var(False)
    """Whether the user is picking a widget to inspect."""

    def __init__(self):
        """Initialise the inspector."""

        super().__init__()

        self._highlight_boxes: dict[Widget, dict[str, Container]] = {}
        """Extra elements added to highlight the border/margin/padding of the widget being inspected."""
        self._highlight_styles: dict[Widget, OriginalStyles] = {}
        """Stores the original styles of any hovered widgets. Unrelated to _highlight_boxes."""

    def compose(self) -> ComposeResult:
        """Add sub-widgets."""
        inspect_icon = "⇱" # Alternatives: 🔍 🎯 🮰 🮵 ⮹ ⇱ 🢄 🡴 🡤 🡔 🢰 (↖️ arrow emoji unreliable)
        # expand_icon = "+" # Alternatives: + ⨁ 🪜 🎊 🐡 🔬 (↕️ arrow emoji unreliable)
        yield Button(f"{inspect_icon} Inspect Element", classes="inspect_button")
        # yield Button(f"{expand_icon} Expand All Visible", classes="expand_all_button")
        yield DOMTree(self.app)  # type: ignore
        yield NodeInfo()
        yield ResizeHandle(self, "left")

    def watch_picking(self, picking: bool) -> None:
        """Watch the picking variable."""
        self.reset_highlight()
        if picking:
            self.capture_mouse()
        else:
            self.release_mouse()
        self.query_one(".inspect_button", Button).set_class(picking, "picking")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button being clicked."""
        if event.button.has_class("expand_all_button"):
            self.query_one(DOMTree).root.expand_all()
        elif event.button.has_class("inspect_button"):
            self.picking = not self.picking

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Handle the mouse moving."""
        if not self.picking:
            return
        self.highlight(self.get_widget_under_mouse(event.screen_offset))

    def get_widget_under_mouse(self, screen_offset: Offset) -> Widget | None:
        """Get the widget under the mouse, ignoring the inspector's highlights and (optionally) the inspector panel."""
        for widget, _ in self.screen.get_widgets_at(*screen_offset):  # type: ignore
            if widget.has_class("inspector_highlight") or (
                self in widget.ancestors_with_self and not ALLOW_INSPECTING_INSPECTOR
            ):
                continue
            return widget
        return None

    async def on_mouse_down(self, event: events.MouseDown) -> None:
        """Handle the mouse being pressed."""
        self.reset_highlight()
        if not self.picking:
            return
        leaf_widget = self.get_widget_under_mouse(event.screen_offset)
        self.picking = False

        if leaf_widget is None:
            return

        # `with self.prevent(DOMTree.Hovered):` would prevent the event from firing at all.
        # We just want to prevent the highlight from being shown in on_domtree_hovered.
        self._prevent_highlight = True

        # Expand the tree to the selected widget.
        await self.query_one(DOMTree).expand_to_dom_node(leaf_widget)

        def focus_and_clear_prevent_highlight() -> None:
            """Focus the DOMTree, and clear the _prevent_highlight flag. Both of these things seem to need a delay."""
            print("focus_and_clear_prevent_highlight", hasattr(self, "_prevent_highlight"))
            self.query_one(DOMTree).focus()
            if hasattr(self, "_prevent_highlight"):
                del self._prevent_highlight
        # self.call_later(clear_prevent_highlight) # Too early.
        # self.call_after_refresh(clear_prevent_highlight) # Too early.
        # self.set_timer(0.1, clear_prevent_highlight) # Not super happy with this...
        # call_later waits for messages to be processed within a specific object,
        # so maybe I can wait for the DOMTree...
        # self.query_one(DOMTree).call_later(clear_prevent_highlight)
        # That seems to work! ...Sometimes!
        # Maybe it should wait for both the DOMTree and the Inspector...
        # def wait_for_domtree() -> None:
        #     print("wait_for_domtree", hasattr(self, "_prevent_highlight"))
        #     self.query_one(DOMTree).call_later(clear_prevent_highlight)
        # self.call_later(wait_for_domtree)
        # Still unreliable. Just use a timer for now.
        self.set_timer(0.1, focus_and_clear_prevent_highlight)

    def on_domtree_selected(self, event: DOMTree.Selected) -> None:
        """Handle a node being selected in the DOM tree."""
        print("Inspecting DOM node:", event.dom_node)
        self.query_one(NodeInfo).dom_node = event.dom_node

    def on_domtree_hovered(self, event: DOMTree.Hovered) -> None:
        """Handle a DOM node being hovered/highlighted."""
        self.highlight(event.dom_node)

    async def on_node_info_follow_link_to_node(self, event: NodeInfo.FollowLinkToNode) -> None:
        """Handle a link being clicked in the NodeInfo panel."""
        await self.query_one(DOMTree).expand_to_dom_node(event.dom_node)

    def reset_highlight(self, except_widgets: Iterable[Widget] = ()) -> None:
        """Reset the highlight."""
        for widget in self._highlight_boxes:
            if widget in except_widgets:
                continue
            added_widgets = self._highlight_boxes[widget]
            for added_widget in added_widgets.values():
                added_widget.remove()
        for widget, old in list(self._highlight_styles.items()):
            if widget in except_widgets:
                continue
            # widget.styles.border = old.border
            # widget.border_title = old.border_title
            # widget.styles.background = old.background
            widget.styles.tint = old.tint
            del self._highlight_styles[widget]

    def is_list_of_widgets(self, value: Any) -> TypeGuard[list[Widget]]:
        """Test whether a value is a list of widgets. The TypeGuard tells the type checker that this function ensures the type."""
        if not isinstance(value, list):
            return False
        for item in value:  # type: ignore
            if not isinstance(item, Widget):
                return False
        return True

    def highlight(self, dom_node: DOMNode | None) -> None:
        """Highlight a DOM node."""
        print("highlight")
        import traceback
        traceback.print_stack(limit=2)

        if hasattr(self, "_prevent_highlight") and dom_node is not None:
            print("highlight prevented")
            del self._prevent_highlight
            return
        print("Highlighting DOM node:", dom_node)

        if not isinstance(dom_node, Widget):
            # Only widgets have a region, App (the root) doesn't.
            self.reset_highlight()
            return
        
        # Rainbow highlight of ancestors.
        """
        if dom_node and dom_node is not self.screen:
            for i, widget in enumerate(dom_node.ancestors_with_self):
                if not isinstance(widget, Widget):
                    continue
                self._highlight_styles[widget] = OriginalStyles(
                    background=widget.styles.background,
                    border=widget.styles.border,
                    border_title=widget.border_title,
                    tint=widget.styles.tint,
                ))
                # widget.styles.background = Color.from_hsl(i / 10, 1, 0.3)
                # if not event.ctrl:
                # widget.styles.border = ("round", Color.from_hsl(i / 10, 1, 0.5))
                # widget.border_title = widget.css_identifier_styled
                widget.styles.tint = Color.from_hsl(i / 10, 1, 0.5).with_alpha(0.5)
        """

        # Tint highlight of hovered widget, and descendants, since the tint of a parent isn't inherited.
        widgets = dom_node.walk_children(with_self=True)
        assert self.is_list_of_widgets(widgets), "walk_children should return a list of widgets, but got: " + repr(widgets)
        self.reset_highlight(except_widgets=widgets)
        for widget in widgets:
            if widget in self._highlight_styles:
                continue
            self._highlight_styles[widget] = OriginalStyles(
                # background=widget.styles.inline.background if widget.styles.inline.has_rule("background") else None,
                # border=widget.styles.inline.border if widget.styles.inline.has_rule("border") else None,
                # border_title=widget.border_title,
                tint=widget.styles.inline.tint if widget.styles.inline.has_rule("tint") else None,
            )
            widget.styles.tint = Color.parse("aquamarine").with_alpha(0.5)

        # Highlight the clipped region of the hovered widget.
        # TODO: Highlight the metrics of the hovered widget: padding, border, margin.

        if "inspector_highlight" not in self.app.styles.layers: # type: ignore
            self.app.styles.layers += ("inspector_highlight",) # type: ignore
        
        if dom_node not in self._highlight_boxes:
            self._highlight_boxes[dom_node] = {}
        used_boxes: list[Container] = []
        def show_box(name: str, region: Region, color: str) -> None:
            """Draw a box to the screen, re-using an old one if possible."""
            assert isinstance(dom_node, Widget), "dom_node needed for association with highlight box, but got: " + repr(dom_node)
            try:
                box = self._highlight_boxes[dom_node][name]
            except KeyError:
                box = Container(classes="inspector_highlight")
                self._highlight_boxes[dom_node][name] = box
            # The alpha doesn't actually blend with what's behind it, just a solid background.
            # Still, it's better with it, since it responds to the theme (dark/light).
            box.styles.background = Color.parse(color).with_alpha(0.5)
            box.styles.width = region.width
            box.styles.height = region.height
            box.styles.offset = (region.x, region.y)
            box.styles.layer = "inspector_highlight"
            # box.styles.dock = "top" # "Literal['top']" is incompatible with "str | None"
            # box.styles.dock = cast(str, "top") # "str" is incompatible with "str | None"
            # box.styles.dock = cast(str | None, "top") # "str | None" is incompatible with "str | None"
            box.styles.dock = "top" # type: ignore
            self.app.mount(box) # type: ignore
            used_boxes.append(box)

        # show_box("region", dom_node.region, "blue")
        # show_box("scrollable_content_region", dom_node.scrollable_content_region, "red")
        try:
            map_geometry = self.screen.find_widget(dom_node) # type: ignore
        except NoWidget:
            return
        # Show the hovered widget's region, as it extends OUTSIDE of the clip region
        # (i.e. excluding what's normally visible, showing only the overflow),
        # and excluding the region of the inspector itself, since overlap causes confusion.
        regions = subtract_multiple_regions(map_geometry.region, [map_geometry.clip, self.region])
        for index, region in enumerate(regions):
            show_box(f"clipped:{index}", region, "aquamarine")
        # remove unused boxes
        # including boxes associated with an old dom_node
        for dom_node, boxes in list(self._highlight_boxes.items()):
            for name, box in list(boxes.items()):
                if box not in used_boxes:
                    box.remove()
                    del self._highlight_boxes[dom_node][name]
            if not self._highlight_boxes[dom_node]:
                del self._highlight_boxes[dom_node]
