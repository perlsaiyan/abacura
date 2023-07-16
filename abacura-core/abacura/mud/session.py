"""MUD session handler"""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
import re
import shlex
import time
from importlib import import_module
from typing import TYPE_CHECKING, Optional, List, Any, AnyStr, Generator

from rich.text import Text
from rich.segment import Segment, Segments
from rich.style import Style
from serum import inject, Context
from textual import log
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import TextLog

from abacura.widgets import InputBar
from abacura.screens import SessionScreen
from abacura.config import Config
from abacura.mud import BaseSession, OutputMessage
from abacura.mud.options import GA
from abacura.mud.logger import LOKLogger
from abacura.mud.options.msdp import MSDP
from abacura.plugins import command, ContextProvider
from abacura.plugins.director import Director
from abacura.plugins.events import AbacuraMessage
from abacura.plugins.loader import PluginLoader
from abacura.utils.ring_buffer import RingBufferLogSql
from abacura.utils.fifo_buffer import FIFOBuffer
from abacura.widgets.footer import AbacuraFooter

if TYPE_CHECKING:
    from abacura.abacura import Abacura

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


@inject
class Session(BaseSession):
    """Main User Session Class"""

    # Injected Objects
    config: Config
    abacura: Abacura

    def __init__(self, name: str):

        self.name = name
        self.host = None
        self.port = None
        self.tl: Optional[TextLog] = None
        self.debugtl: Optional[TextLog] = None
        self.output_buffer: FIFOBuffer = FIFOBuffer(1000)

        self.core_msdp: MSDP = MSDP(self.output, self.send, self)
        self.options = {}

        self.plugin_loader: Optional[PluginLoader] = None
        self.ring_buffer: Optional[RingBufferLogSql] = None

        self.last_socket_write: float = time.monotonic()
        self.outb = b''
        self.writer = None
        self.connected = False
        self.command_char = self.config.get_specific_option(self.name, "command_char", "#")

        self.speedwalk_re = re.compile(speedwalk_pattern)
        self.speedwalk_step_re = re.compile(speedwalk_step_pattern)

        self.loklog = LOKLogger(self.name, self.config)

        with Context(session=self):
            self.director: Director = Director()
            self.director.register_object(self)

        self.dispatcher = self.director.event_manager.dispatcher
        self.listener = self.director.event_manager.listener

        core_injections = {"config": self.config, "session": self, "app": self.abacura,
                           "sessions": self.abacura.sessions, "core_msdp": self.core_msdp,
                           "director": self.director, "scripts": self.director.script_provider,
                           "buffer": self.output_buffer}
        self.core_plugin_context = Context(**core_injections)

        additional_injections = {}
        session_modules = self.config.get_specific_option(self.name, "modules")
        if session_modules:
            for ses_mod in session_modules:
                sm = import_module(ses_mod)
                if hasattr(sm, "__CONTEXT_PROVIDER"):
                    ctx = getattr(sm, "__CONTEXT_PROVIDER")
                    sm_cls = load_class(ctx, ContextProvider)
                    additional_injections.update(sm_cls(self.config, self.name).get_injections())
        self.additional_plugin_context = Context(**core_injections, **additional_injections)

        screen_class = load_class(self.config.get_specific_option(self.name, "screen_class", ""), SessionScreen)

        with self.additional_plugin_context:
            self.screen = screen_class(name)
            self.abacura.install_screen(self.screen, name=name)

        if ring_filename := self.config.ring_log(name):
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

        self.plugin_loader = PluginLoader()
        self.plugin_loader.load_plugins(modules=["abacura"], plugin_context=self.core_plugin_context)

        session_modules = self.config.get_specific_option(self.name, "modules")
        if isinstance(session_modules, list):
            self.plugin_loader.load_plugins(session_modules, plugin_context=self.additional_plugin_context)

    # TODO: Need a better way of handling this, possibly an autoloader
    def register_options(self):
        """Set up telnet options handlers"""
        # TODO swap to context?
        self.options[self.core_msdp.code] = self.core_msdp

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

    def player_input(self, line, gag: bool = False) -> None:
        """This is entry point of the inputbar on the screen"""        
        echo_color = "" if gag else "white"
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

            log(f"Yo do {cmd} from {sl} from {line}")
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

    def send(self, msg: str, raw: bool = False, echo_color: str = "orange1") -> None:
        """Send to writer (socket), raw will send the message without byte translation"""
        if self.writer is not None:
            try:
                if raw:
                    self.writer.write(msg)
                else:
                    self.writer.write(bytes(msg + "\n", "UTF-8"))
                self.last_socket_write = time.monotonic()

                if echo_color:
                    self.echo_command(msg.rstrip("\n"), echo_color)

            except BrokenPipeError:
                self.connected = False
                self.output(f"[bold red]# Lost connection to server.", markup=True)
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
    def debuglog_command(self, _facility: str = "info", msg: str = "", markup: bool = True, highlight: bool=True):
        """
        Send output to debug window

        :facility optional facility, defaults to 'info'
        :markup use rich markup
        :highlight use rich highlighting
        :param msg message to log
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
        self.output_buffer.append(message)

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

    # TODO move this into a separate thing, it's getting too long
    async def telnet_client(self, host: str, port: int) -> None:
        """async worker to handle input/output on socket"""
        self.host = host
        self.port = port

        while self.tl is None:
            log.warning("TL not available, sleeping 0.1 second before connection")
            await asyncio.sleep(0.1)

        log.info(f"Session {self.name} connecting to {host} {port}")
        try:
            reader, self.writer = await asyncio.open_connection(host, port)
            self.connected = True
        except TimeoutError:
            self.loklog.warn(f"Connection timeout from {host}:{port}")
            self.output(f"[bold red]# Connection refused {host}:{port}", markup=True)
        except ConnectionRefusedError:
            self.loklog.warn(f"Connection refused from {host}:{port}")
            self.output(f"[bold red]# Connection refused {host}:{port}", markup=True)

        self.register_options()
        self.poll_timeout = 0.001
        self.go_ahead = self.config.get_specific_option(self.name, "ga")

        while self.connected is True:

            # We read one character at a time so that we can find IAC sequences
            # We use wait_for() so we can work with muds that don't use GA
            try:
                if self.go_ahead:
                    data = await reader.read(1)
                else:
                    data = await asyncio.wait_for(reader.read(1), self.poll_timeout)
            except BrokenPipeError:
                self.output("[bold red]# Lost connection to server.", markup=True)
                self.connected = False
                return
            except ConnectionResetError:
                self.output("[bold red]# Connection reset by peer.", markup=True)
                self.connected = False
                return
            except asyncio.TimeoutError:
                if len(self.outb) > 0:
                    self.output(self.outb.decode("UTF-8", errors="ignore"), ansi=True)
                    self.outb = b''
                    self.poll_timeout = 0.001
                else:
                    if self.poll_timeout < 0.05:
                        self.poll_timeout *= 2
                        log.debug(f"timeout {self.poll_timeout}")
                continue

            # Empty string means we lost our connection
            if data == b'':
                self.output("[bold red]# Lost connection to server.", markup=True)
                self.connected = False

            # End of a MUD line in buffer, send for processing
            elif data == b'\n':
                self.output(self.outb.decode("UTF-8", errors="ignore").replace("\r", " "), ansi=True)
                self.outb = b''

            # handle IAC sequences
            elif data == b'\xff':
                data = await reader.read(1)
                log.debug(f"IAC {data}")
                # IAC DO
                if data == b'\xfd':
                    data = await reader.read(1)

                    if ord(data) in self.options:
                        self.options[ord(data)].do()
                    else:
                        if data == b'\x18':
                            # TTYPE

                            self.writer.write(b'\xff\xfb\x18')
                            #self.output("IAC WILL TTYPE")
                        elif data == b'\x1f':
                            # IAC WON'T NAWS
                            self.writer.write(b'\xff\xfc\x1f')
                            #self.output("IAC WON'T NAWS")
                        else:
                            pass
                            #self.output(f"IAC DO {ord(data)}")

                # IAC DONT
                if data == b'\xfe':
                    data = await reader.read(1)
                    #self.output(f"IAC DONT {data}")

                # IAC WILL
                elif data == b'\xfb':
                    data = await reader.read(1)
                    if ord(data) in self.options:
                        self.options[ord(data)].will()
                    elif ord(data) == 1:
                        self.dispatcher(AbacuraMessage(event_type="core.password_mode", value="on"))
                    else:
                        pass
                        #self.output(f"IAC WILL {ord(data)}")

                # IAC WONT
                elif data == b'\xfc':
                    data = await reader.read(1)
                    #self.output(f"IAC WONT {data}")
                    if ord(data) == 1:
                        self.dispatcher(AbacuraMessage(event_type="core.password_mode", value="off"))
                # SB
                elif data == b'\xfa':
                    c = await reader.read(1)
                    data = c
                    buf = b''
                    while c != b'\xf0':
                        buf = buf + c
                        c = await reader.read(1)
                    if ord(data) in self.options:
                        self.options[ord(data)].sb(buf)
                    else:
                        pass
                        #self.output(f"IAC SB {buf}")

                # TTYPE
                elif data == b'\x18':
                    pass
                    #self.output(f"IAC TTYPE")

                # NAWS
                elif data == b'\x1f':
                    #self.output(f"IAC NAWS")
                    pass

                # telnet GA sequence, likely end of prompt
                elif data == GA:
                    self.output(self.outb.decode("UTF-8", errors="ignore"), ansi=True)
                    self.dispatcher(AbacuraMessage("core.prompt", self.outb.decode("UTF-8", errors="ignore")))
                    self.output("")

                    self.outb = b''

                # IAC UNKNOWN
                else:
                    pass
                    #self.output(f"IAC UNKNOWN {ord(data)}")

            # Catch everything else in our buffer and hold it
            else:
                self.outb = self.outb + data

    @command
    def connect(self, name: str, host: str = '', port: int = 0) -> None:
        """@connect <name> <host> <port> to connect a game session"""

        if not host:
            host = self.config.get_specific_option(name, "host")
            try:
                port = int(self.config.get_specific_option(name, "port"))
            except TypeError:
                port = None

        log(f"connect: {name} {host}:{port}")

        if name in self.abacura.sessions:
            self.output("[bold red]# SESSION ALREADY EXISTS", markup=True)
        elif name not in self.config.config and (not host or not port):
            self.output(" [bold red]#connect <session name> <host> <port>", markup=True, highlight=True)
        else:
            self.abacura.create_session(name)
            if host and port:
                self.abacura.run_worker(self.abacura.sessions[name].telnet_client(host, port),
                                        name=f"socket-{name}", group=name,
                                        #exit_on_error=False,
                                        description=f"Mud connection for {name} ({host}:{port})")
            else:
                log(f"Session: {name} created in disconnected state due to no host or port")

    @command(name="session")
    # Do not name this function "session" or you'll overwrite self.session :)
    def session_command(self, name: str = "") -> None:
        """@session <name>: Get information about sessions or swap to session <name>"""
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
