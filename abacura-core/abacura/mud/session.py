"""MUD session handler"""
from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime
from importlib import import_module
from typing import TYPE_CHECKING, Optional, Union, Any, Generator

from rich.segment import Segment, Segments
from rich.style import Style
from rich.text import Text
from textual import log
from textual.css.query import NoMatches
from textual.strip import Strip
from textual.widgets import TextLog

from abacura.config import Config
from abacura.mud import BaseSession, OutputMessage
from abacura.mud.logger import LOKLogger
from abacura.mud.options.msdp import MSDP
from abacura.plugins import command, ContextProvider
from abacura.plugins.director import Director
from abacura.plugins.loader import PluginLoader
from abacura.plugins.task_queue import QueueManager
from abacura.screens import SessionScreen
from abacura.utils.fifo_buffer import FIFOBuffer
from abacura.utils.ring_buffer import RingBufferLogSql
from abacura.widgets.footer import AbacuraFooter

if TYPE_CHECKING:
    from abacura.abacura import Abacura
    from asyncio import StreamWriter

speedwalk_pattern = r'^(\d*[neswud])+$'
speedwalk_step_pattern = r'\d*[neswud]'


def load_class(class_name: str, default=None):
    """dynamically load a class"""
    if not class_name:
        return default

    pkg, class_path = class_name.rsplit(".", 1)
    log(f"Importing {class_path} from {pkg}")
    class_module = import_module(pkg)

    cls = getattr(class_module, class_path, None)
    if not cls:
        raise ValueError(f"Unable to load {class_name}")
    return cls


class Session(BaseSession):
    """Main User Session Class"""

    def __init__(self, name: str, abacura: Abacura, config: Config):
        self.abacura = abacura
        self.config = config
        self.name = name
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.tl: Optional[TextLog] = None
        self.debugtl: Optional[TextLog] = None
        self.output_history: FIFOBuffer = FIFOBuffer(1000)

        self.core_msdp: MSDP = MSDP(self.output, self.send, self)
        self.options = {}

        self.plugin_loader: PluginLoader = PluginLoader()
        self.last_socket_write: float = time.monotonic()

        self.writer = None
        self.connected = False
        self.command_char = self.config.get_specific_option(self.name, "command_char", "#")

        self.speedwalk_re = re.compile(speedwalk_pattern)
        self.speedwalk_step_re = re.compile(speedwalk_step_pattern)

        self.loklog = LOKLogger(self.name, self.config)

        self.director: Director = Director(session=self)
        self.director.register_object(obj=self)

        self.dispatch = self.director.event_manager.dispatch
        self.add_listener = self.director.event_manager.add_listener

        core_injections = {"config": self.config, "session": self, "app": self.abacura,
                           "sessions": self.abacura.sessions, "core_msdp": self.core_msdp,
                           "cq": QueueManager(),
                           "director": self.director, "buffer": self.output_history}
        self.core_plugin_context = core_injections

        additional_injections = {}
        session_modules = self.config.get_specific_option(self.name, "modules")
        if session_modules:
            for ses_mod in session_modules:
                sm = import_module(ses_mod)
                if hasattr(sm, "__CONTEXT_PROVIDER"):
                    ctx = getattr(sm, "__CONTEXT_PROVIDER")
                    sm_cls = load_class(ctx, ContextProvider)
                    additional_injections.update(sm_cls(self.config, self.name).get_injections())

        self.additional_plugin_context = {**core_injections, **additional_injections}

        screen_class = load_class(self.config.get_specific_option(self.name, "screen_class", ""), SessionScreen)

        self.screen = screen_class(name, self)
        self.abacura.install_screen(self.screen, name=name)

        ring_filename = self.config.ring_log(name) or ":memory:"
        ring_size = self.config.get_specific_option(name, "ring_size", 10000)
        self.ring_buffer = RingBufferLogSql(ring_filename, ring_size)

        self.abacura.push_screen(name)
        self.screen.set_interval(interval=0.01, callback=self.director.ticker_manager.process_tick, name="tickers")

    # TODO: This doesn't launch a screen anymore, it loads plugins
    def launch_screen(self):
        """Fired on screen mounting, so our Footer is updated and Session gets a TextLog handle"""
        self.screen.query_one(AbacuraFooter).session = self.name
        self.tl = self.screen.query_one(f"#output-{self.name}", expect_type=TextLog)
        try:
            self.debugtl = self.screen.query_one("#debug", expect_type=TextLog)
        except NoMatches:
            pass

        self.plugin_loader.load_plugins(modules=["abacura"], plugin_context=self.core_plugin_context)

        session_modules = self.config.get_specific_option(self.name, "modules")
        if isinstance(session_modules, list):
            self.plugin_loader.load_plugins(session_modules, plugin_context=self.additional_plugin_context)

        telnet_client = self.plugin_loader.plugins["TelnetPlugin"].plugin.telnet_client
        if self.host and self.port:
            log.warning(f"Attempting connection to {self.host} and {self.port} for {self.name}")
            self.abacura.run_worker(
                telnet_client(self.host, self.port, handlers=[self.core_msdp]),
                name=f"socket-{self.name}", group=self.name,
                description=f"Mud connection for {self.name} ({self.host}:{self.port})")
        else:
            log(f"Session: {self.name} created in disconnected state due to no host or port")

    def input_splitter(self, line) -> Generator[str, Any, Any]:
        buf: str = ""

        while line:
            token: str = line[0]
            line = line[1:]

            if token == '\\':
                if len(line) > 0:
                    buf += str(line[0])
                    line = line[1:]
            elif token == ';':
                yield buf
                buf = ""
            else:
                buf += token

        if len(buf) > 0:
            yield buf

    def player_input(self, line, gag: bool = False, echo_color: str = "white") -> None:
        """This is entry point of the inputbar on the screen"""        
        echo_color = "" if gag else echo_color
        sl = line.lstrip()
        if sl == "":
            self.send("\n")
            return
        for sl in self.input_splitter(line):
            sl = sl.rstrip()
            if sl == "":
                cmd = sl
            else:
                cmd = sl.split()[0]

            if cmd.startswith(self.command_char) and self.director.command_manager.execute_command(sl):
                continue

            if self.speedwalk_re.match(sl) and self.connected:
                for walk in self.speedwalk_step_re.findall(sl):
                    # We're keeping delimiters so without a preceding number, first part is ''
                    parts = re.split('([neswud])', walk)
                    if parts[0] == '':
                        self.send(parts[1] + "\n", echo_color=echo_color)
                    else:
                        for _ in range(int(parts[0])):
                            self.send(parts[1] + "\n", echo_color='')
                continue

            if self.director.alias_manager.handle(cmd, sl):
                continue

            if self.connected:
                self.send(sl + "\n", echo_color=echo_color)
                continue

            self.output(f"[bold red]# NO SESSION CONNECTED - pi {sl}", markup=True)

    # TODO raw can come out now that we isinstance
    def send(self, msg: Union[str,bytes], raw: bool = False, echo_color: str = "orange1") -> None:
        """Send to writer (socket)"""
        if self.writer is not None:
            try:
                if isinstance(msg,str):
                    self.writer.write(bytes(msg + "\n", "UTF-8"))
                elif isinstance(msg,bytes):
                    self.writer.write(msg)

                self.last_socket_write = time.monotonic()

                if echo_color:
                    self.echo_command(msg.rstrip("\n"), echo_color)

            except BrokenPipeError:
                self.connected = False
                self.output("[bold red]# Lost connection to server.", markup=True)
        else:
            self.output(f"[bold red]# NO-SESSION SEND: {msg}", markup=True, highlight=True)

    def echo_command(self, cmd, color="white"):
        if not self.tl or not len(self.tl.lines):
            return

        strip = self.tl.lines[-1]
        line_text = "".join([segment.text for segment in strip._segments])
        cmd_segment = Segment(cmd, Style(color=color))
        if not line_text.rstrip().endswith(">"):
            self.output(Segments([cmd_segment]))
            return

        new_segments = strip._segments + [cmd_segment]
        new_strip = Strip(segments=new_segments)
        self.tl.lines[-1] = new_strip
        self.tl._line_cache.clear()
        self.tl.render()

    @command(name="debuglog")
    def debuglog_command(self, msg: str, _facility: str = "info", markup: bool = True, highlight: bool=True):
        """
        Send output to debug window

        :param msg: message to log
        :param _facility: optional facility, defaults to 'info'
        :param markup: use rich markup
        :param highlight: use rich highlighting
        """
        self.debuglog(facility=_facility, msg=msg, markup=markup, highlight=highlight)

    def debuglog(self, facility: str = "info", msg: str= "", markup: bool = True, highlight: bool=True):
        if self.debugtl:
            date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            self.debugtl.markup = markup
            self.debugtl.highlight = highlight
            self.debugtl.write(f"{date_time} \[{facility}]: {msg}")

    def output(self, msg,
               markup: bool = False, highlight: bool = False, ansi: bool = False, actionable: bool = True,
               gag: bool = False, loggable: bool = True):

        """Write to TextLog for this screen"""
        if self.tl is None:
            log.warning(f"Attempt to write to nonexistent TextLog: {msg}")
            return

        message = OutputMessage(msg, gag)
        self.output_history.append(message)

        if actionable:

            if self.director and self.director.action_manager:
                self.director.action_manager.process_output(message)

        if not message.gag:

            self.tl.markup = markup
            self.tl.highlight = highlight
            if ansi:
                self.tl.write(Text.from_ansi(message.message))
            else:
                self.tl.write(message.message)
            self.loklog.info(message.message)

            # TODO: Add location / vnum and any other context to the log
            if self.ring_buffer and loggable:
                self.ring_buffer.log(message)
            self.tl.markup = False
            self.tl.highlight = False


    @command
    def connect(self, name: str, host: str = '', port: int = 0) -> None:
        """
        Connect to a mud and create a session

        :param name: Session name
        :param host: Host Address
        :param port: Host Port
        """

        if not host:
            host = self.config.get_specific_option(name, "host")
            try:
                port = int(self.config.get_specific_option(name, "port"))
            except TypeError:
                port = 0

        log(f"connect: {name} {host}:{port}")

        if name in self.abacura.sessions:
            self.output("[bold red]# SESSION ALREADY EXISTS", markup=True)
        elif name not in self.config.config and (not host or not port):
            self.output(" [bold red]#connect <session name> <host> <port>",
                        markup=True, highlight=True)
        else:
            self.abacura.create_session(name)

        new_ses = self.abacura.sessions[name]
        new_ses.host = host
        new_ses.port = port

    @command(name="session")
    # Do not name this function "session" or you'll overwrite self.session :)
    def session_command(self, name: str = "") -> None:
        """
        List sessions and swap to a new one

        :param name: Swap to another session by name
        """

        if not name:
            buf = "[bold red]# Current Sessions:\n"
            for session_name, session in self.abacura.sessions.items():
                if session_name == self.abacura.session:
                    buf += "[bold green]>[white]"
                else:
                    buf += " [white]"

                if session_name == "null":
                    buf += f"{session.name}: Main Session\n"
                else:
                    if session.connected:
                        buf += f"{session.name}: {session.host} {session.port}\n"
                    else:
                        buf += f"{session.name}: {session.host} {session.port} [red]\\[disconnected]\n"

            self.output(buf, markup=True, highlight=True)
        else:
            if name in self.abacura.sessions:
                self.abacura.set_session(name)
            else:
                self.output(f"[bold red]# INVALID SESSION {name}", markup=True)
