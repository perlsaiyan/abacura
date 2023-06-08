from __future__ import annotations

from abacura import SessionScreen, AbacuraFooter
from abacura.mud import BaseSession
from abacura.mud.options.msdp import MSDP
from abacura.plugins.plugin import PluginManager

import asyncio
from importlib import import_module
import os
import re
import sys

from rich.text import Text
from serum import inject, Context

from textual import log
from textual.screen import Screen

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self
    from abacura.abacura import Abacura

@inject
class Session(BaseSession):
    _config: dict
    
    abacura: Abacura
    all: dict
    outb = b''
    writer = None
    connected = False
    name = ""

    def __init__(self, name: str):

        self.name =  name
        self.host = None
        self.port = None

        with Context(_config=self._config, _session=self):
            if name in self.config and "screen_class" in self.config[name]:
                (package, screen_class) = self.config[name]["screen_class"].rsplit(".",1)
                log(f"Importing a package {package}")
                log(sys.path)
                mod = import_module(package)
                sc = getattr(mod, screen_class)
                self.abacura.install_screen(sc(name), name=name)

            else:
                self.abacura.install_screen(SessionScreen(name), name=name)
        
        self.abacura.push_screen(name)
        self.screen = self.abacura.query_one(f"#screen-{name}", expect_type=Screen)


        
    def launch_screen(self):
        self.screen.query_one(AbacuraFooter).session = self.name
        log(f"stack: {self.abacura.screen_stack}")
        log(f"output should be #output-{self.name}")
        self.tl = self.screen.query_one(f"#output-{self.name}")

        with Context(config = self.config, sessions = self.abacura.sessions, tl=self.tl, app=self.abacura, session=self):
            self.plugin_manager = PluginManager()     
        
    @property
    def config(self):
        return self._config.config
    
    def register_options(self):
        self.options = {}
        msdp = MSDP(self.output, self.writer)
        self.options[msdp.code] = msdp

    def player_input(self, line) -> None:
        
        sl = line.lstrip()
        if sl == "":
            cmd = sl
        else:
            cmd = sl.split()[0]

        if cmd.startswith("@") and self.plugin_manager.handle_command(line):
            return
        
        if self.connected:
            self.send(line + "\n")
            return
        
        self.tl.markup = True
        self.tl.write("[bold red]# NO SESSION CONNECTED")
        self.tl.markup = False

    def send(self, msg: str) -> None:
        if self.writer is not None:
            self.writer.write(bytes(msg + "\n", "UTF-8")) 
    
    def output(self, msg, markup: bool=False, highlight: bool=False):
        self.tl.markup = markup
        self.tl.highlight = highlight
        self.tl.write(Text.from_ansi(msg))
        self.tl.markup = False
        self.tl.highlight =  False

        # TODO temporary action so i can stream and share screen recordings
        if re.match(r'^Please enter your account password', msg) and os.environ.get("MUD_PASSWORD") is not None:
            self.send(os.environ.get("MUD_PASSWORD"))
        elif re.match(r'^Enter your account name. If you do not have an account,', msg) and self.name in self.config and "character_name" in self.config[self.name]:
            self.send(self.config[self.name]["character_name"])

    async def telnet_client(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        reader, self.writer = await asyncio.open_connection(host, port)
        self.connected = True
        self.register_options()
        while self.connected == True:
            data = await reader.read(1)

            if data == b'':
                self.tl.markup = True
                self.tl.write("[bold red]Lost connection to server.")
                self.connected = False

                
            elif data == b'\n':
                self.output(self.outb.decode("UTF-8", errors="ignore").replace("\r"," "))
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

                elif data == b'\xf9':
                    self.output(self.outb.decode("UTF-8", errors="ignore"))
                    self.output("")
                    self.outb = b''

                # IAC UNKNOWN
                else:
                    pass
                    #self.output(f"IAC UNKNOWN {ord(data)}")

            # Catch everything else in our buffer        
            else:
                self.outb = self.outb + data

