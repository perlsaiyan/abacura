"""MUD session handler"""
from __future__ import annotations

import asyncio
from importlib import import_module
import os
import re
import sys
import time

from typing import TYPE_CHECKING, Optional

from rich.text import Text
from serum import inject, Context
from textual import log
from textual.screen import Screen

from abacura.utils.ring_buffer import RingBufferLogSql
from abacura import SessionScreen, AbacuraFooter
from abacura.config import Config
from abacura.mud import BaseSession, OutputMessage
from abacura.mud.options import GA
from abacura.mud.options.msdp import MSDP
from abacura.plugins.director import Director
from abacura.plugins.loader import PluginLoader
from abacura.plugins import command
from abacura.plugins.events import EventManager

if TYPE_CHECKING:
    from abacura.abacura import Abacura


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
        self.tl: Optional[log] = None
        self.core_msdp: MSDP = MSDP(self.output, self.send, self)
        self.options = {}
        self.event_manager: EventManager = EventManager()
        self.dispatcher = self.event_manager.dispatcher
        self.listener = self.event_manager.listener
        self.director: Optional[Director] = None
        self.plugin_loader: Optional[PluginLoader] = None
        self.ring_buffer: Optional[RingBufferLogSql] = None

        self.outb = b''
        self.writer = None
        self.connected = False

        with Context(session=self):
            self.director = Director()
            self.director.register_object(self)

        self.plugin_context: Context = Context(config=self.config, session=self, app=self.abacura,
                                               sessions=self.abacura.sessions, core_msdp=self.core_msdp,
                                               director=self.director)

        with self.plugin_context:
            if self.config.get_specific_option(name, "screen_class"):
                (package, screen_class) = self.config.get_specific_option(name, "screen_class").rsplit(".", 1)
                log(f"Importing a package {package}")
                log(sys.path)
                mod = import_module(package)
                user_screen = getattr(mod, screen_class)
                self.abacura.install_screen(user_screen(name), name=name)

            else:
                self.abacura.install_screen(SessionScreen(name), name=name)

        if ring_filename := self.config.get_specific_option(name, "ring_filename"):
            ring_size = self.config.get_specific_option(name, "ring_size", 10000)
            self.ring_buffer = RingBufferLogSql(ring_filename, ring_size)

        self.abacura.push_screen(name)
        self.screen = self.abacura.query_one(f"#screen-{name}", expect_type=Screen)

    # TODO: This should possibly be an Message from the SessionScreen
    def launch_screen(self):
        """Fired on screen mounting, so our Footer is updated and Session gets a TextLog handle"""
        self.screen.query_one(AbacuraFooter).session = self.name

        while self.tl is None:
            self.tl = self.screen.query_one(f"#output-{self.name}")
            time.sleep(1)

        with self.plugin_context:
            self.plugin_loader = PluginLoader()
            self.plugin_loader.load_plugins()
            self.screen.set_interval(interval=0.01, callback=self.director.ticker_manager.process_tick, name="tickers")

    # TODO: Need a better way of handling this, possibly an autoloader
    def register_options(self):
        """Set up telnet options handlers"""
        # TODO swap to context?
        self.options[self.core_msdp.code] = self.core_msdp

    def player_input(self, line) -> None:
        """This is entry point of the inputbar on the screen"""        
        sl = line.lstrip()
        if sl == "":
            cmd = sl
        else:
            cmd = sl.split()[0]

        if cmd.startswith("@") and self.director.command_manager.execute_command(line):
            return

        if self.director.alias_manager.handle(cmd, sl):
            return

        if self.connected:
            self.send(line + "\n")
            return

        self.tl.markup = True
        self.tl.write("[bold red]# NO SESSION CONNECTED")
        self.tl.markup = False

    def send(self, msg: str, raw: bool = False) -> None:
        """Send to writer (socket), raw will send the message without byte translation"""
        if self.writer is not None:
            try:
                if raw:
                    self.writer.write(msg)
                else:
                    self.writer.write(bytes(msg + "\n", "UTF-8"))
            except BrokenPipeError:
                self.connected = False
                self.output(f"[bold red]# Lost connection to server.", markup=True)
        else:
            self.output(f"[bold red]# NO-SESSION SEND: {msg}", markup=True, highlight=True)

    def output(self, msg,
               markup: bool = False, highlight: bool = False, ansi: bool = False, actionable: bool = True,
               gag: bool = False, loggable: bool = True):

        """Write to TextLog for this screen"""
        if self.tl is None:
            log.warning(f"Attempt to write to nonexistent TextLog: {msg}")
            return

        message = OutputMessage(msg, gag)

        if actionable:

            # TODO (REMOVE after plugins fixed) temporary action so i can stream and share screen recordings
            if re.match(r'^Please enter your account password', msg) and os.environ.get("MUD_PASSWORD") is not None:
                self.send(os.environ.get("MUD_PASSWORD"))
            elif re.match(r'^Enter your account name. If you do not have an account,', msg) and self.config.get_specific_option(self.name, "account_name"):
                self.send(self.config.get_specific_option(self.name, "account_name"))

            if self.director and self.director.action_manager:
                self.director.action_manager.process_output(message)

        if not message.gag:
            self.tl.markup = markup
            self.tl.highlight = highlight
            if ansi:
                self.tl.write(Text.from_ansi(message.message))
            else:
                self.tl.write(message.message)

            # TODO: Add location / vnum and any other context to the log
            if self.ring_buffer and loggable:
                self.ring_buffer.log(message)
            self.tl.markup = False
            self.tl.highlight = False

    async def telnet_client(self, host: str, port: int) -> None:
        """async worker to handle input/output on socket"""
        self.host = host
        self.port = port

        while self.tl is None:
            log.warning("TL not available, sleeping 1 second before connection")
            await asyncio.sleep(1)

        log.info(f"Session {self.name} connecting to {host} {port}")
        reader, self.writer = await asyncio.open_connection(host, port)
        self.connected = True
        self.register_options()
        while self.connected is True:

            # We read one character at a time so that we can find IAC sequences
            try:
                data = await reader.read(1)
            except BrokenPipeError:
                self.output("[bold red]# Lost connection to server.", markup=True)
                self.connected = False
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
                    else:
                        pass
                        #self.output(f"IAC WILL {ord(data)}")

                # IAC WONT
                elif data == b'\xfc':
                    data = await reader.read(1)
                    #self.output(f"IAC WONT {data}")

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
                self.abacura.run_worker(self.abacura.sessions[name].telnet_client(host, port))
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
