import asyncio
from textual import log
from typing import TYPE_CHECKING

from abacura.mud.options import GA, TelnetOption
from abacura.mud.options.ttype import TerminalTypeOption
from abacura.plugins import Plugin
from abacura.plugins.events import AbacuraMessage

class TelnetPlugin(Plugin):
    """Handles telnet connectivity"""
    def __init__(self):
        super().__init__()
        self.options: dict[int, TelnetOption] = {}
        self.poll_timeout = 0.001
        self.go_ahead = self.config.get_specific_option(self.session.name, "ga")
        self.connected = False
        self.outb = b''

    # TODO: Need a better way of handling this, possibly an autoloader
    def register_options(self, handlers: list[TelnetOption]):
        """Set up telnet options handlers"""
        # TODO swap to context?
        for handler in handlers:
            self.options[handler.code] = handler

        ttype = TerminalTypeOption(self.session.writer)
        self.options[ttype.code] = ttype

    # TODO move this into a separate thing, it's getting too long
    async def telnet_client(self, host: str, port: int, handlers: list[TelnetOption]) -> None:
        """async worker to handle input/output on socket"""

        log.info(f"Session {self.session.name} connecting to {host} {port} with {handlers}")
        try:
            reader, writer = await asyncio.open_connection(host, port)
            self.session.writer = writer
            self.session.connected = True
            self.connected = True
        except TimeoutError:
            log.warning(f"Connection timeout from {host}:{port}")
            self.session.show_error("Connection timeout {host}:{port}")
            return
        except ConnectionRefusedError:
            log.warning(f"Connection refused from {host}:{port}")
            self.session.show_error("Connection refused {host}:{port}")
            return

        self.register_options(handlers)


        while self.connected is True:

            # We read one character at a time so that we can find IAC sequences
            # We use wait_for() so we can work with muds that don't use GA
            try:
                if self.go_ahead:
                    data = await reader.read(1)
                else:
                    data = await asyncio.wait_for(reader.read(1), timeout=self.poll_timeout)
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
                    self.output(self.outb.decode("UTF-8", errors="ignore").replace("\r", " ").replace("\t", "        "), ansi=True)
                    self.outb = b''
                    self.poll_timeout = 0.001
                else:
                    if self.poll_timeout < 0.05:
                        self.poll_timeout *= 2
                        log.debug(f"timeout {self.poll_timeout}")
                continue

            # Empty string means we lost our connection
            if data == b'':
                self.session.show_error("Lost connection to server.")
                self.connected = False

            # End of a MUD line in buffer, send for processing
            elif data == b'\n':
                self.output(self.outb.decode("UTF-8", errors="ignore").replace("\r", " ").replace("\t", "        "), ansi=True)
                self.outb = b''

            # handle IAC sequences
            elif data == b'\xff':
                data = await reader.read(1)

                # IAC DO
                if data == b'\xfd':
                    data = await reader.read(1)

                    if ord(data) in self.options:
                        log.debug(f"IAC DO for {self.options[ord(data)].name}")
                        self.options[ord(data)].do()
                    else:
                        if data == b'\x1f':
                            # IAC WON'T NAWS
                            writer.write(b'\xff\xfc\x1f')
                            #self.output("IAC WON'T NAWS")
                        else:
                            pass
                            #self.output(f"IAC DO {ord(data)}")

                # IAC DONT
                if data == b'\xfe':
                    data = await reader.read(1)
                    if ord(data) in self.options:
                        log.debug(f"IAC DONT for {self.options[ord(data)].name}")
                        self.options[ord(data)].dont()
                # IAC WILL
                elif data == b'\xfb':
                    data = await reader.read(1)
                    if ord(data) in self.options:
                        log.debug(f"IAC WILL for {self.options[ord(data)].name}")
                        self.options[ord(data)].will()
                    elif ord(data) == 1:
                        self.dispatch(AbacuraMessage(event_type="core.password_mode", value="on"))
                    else:
                        writer.write(b'\xff\xfb' + data)
                        log.debug(f"IAC WILL for Unknown ({ord(data)})")

                # IAC WONT
                elif data == b'\xfc':
                    data = await reader.read(1)
                    #self.output(f"IAC WONT {data}")
                    if ord(data) in self.options:
                        log.debug(f"IAC WILL for {self.options[ord(data)].name}")
                        self.options[ord(data)].wont()
                    elif ord(data) == 1:
                        self.dispatch(AbacuraMessage(event_type="core.password_mode", value="off"))
                # SB
                elif data == b'\xfa':
                    c = await reader.read(1)
                    data = c
                    buf = b''
                    while c != b'\xf0':
                        buf = buf + c
                        c = await reader.read(1)
                    if ord(data) in self.options:
                        log.debug(f"IAC SB for {self.options[ord(data)].name}")
                        self.options[ord(data)].sb(buf)
                    else:
                        log.debug(f"IAC SB for Unknown ({ord(data)})")

                # TTYPE
                #elif data == b'\x18':
                #    writer.write(b'{IAC}')
                #    #self.output(f"IAC TTYPE")

                # NAWS
                elif data == b'\x1f':
                    #self.output(f"IAC NAWS")
                    pass

                # telnet GA sequence, likely end of prompt
                elif data == GA:
                    self.output(self.outb.decode("UTF-8", errors="ignore"), ansi=True)
                    self.dispatch(AbacuraMessage("core.prompt", self.outb.decode("UTF-8", errors="ignore")))
                    # self.output("")

                    self.outb = b''

                # IAC UNKNOWN
                else:
                    log.debug(f"IAC unknown {data}")
                    #self.output(f"IAC UNKNOWN {ord(data)}")

            # Catch everything else in our buffer and hold it
            else:
                self.outb = self.outb + data
