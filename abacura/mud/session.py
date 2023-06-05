import asyncio
import socket
import time
from abacura.mud.options.msdp import MSDP

class Session():
    def __init__(self, name: str):
        self.client = None
        self.outb = b''
        self.writer = None
        self.connected = False
        self.name = name
        self.host = None
        self.port = None

    def register_options(self, handler):
        self.options = {}
        msdp = MSDP(handler, self.writer)
        self.options[msdp.code] = msdp

    def send(self, msg):
        self.writer.write(bytes(msg + "\n", "UTF-8"))
    
    def output(self, msg, markup: bool=False, highlight: bool=False):
        self.handler(self.name, msg, markup=markup, highlight=highlight)

    async def telnet_client(self, handler, host: str, port: int) -> None:
        self.handler = handler
        self.host = host
        self.port = port
        reader, self.writer = await asyncio.open_connection(host, port)
        self.connected = True
        self.register_options(handler)
        while True:
            data = await reader.read(1)

            if data == b'':
                raise Exception("Lost connection to server.")
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
                        match data:
                            # TTYPE
                            case b'\x18':
                                self.writer.write(b'\xff\xfb\x18')
                                self.output("IAC WILL TTYPE")
                            case b'\x1f':
                                # IAC WON'T NAWS
                                self.writer.write(b'\xff\xfc\x1f')
                                self.output("IAC WON'T NAWS")
                            case _:
                                self.output(f"IAC DO {ord(data)}")

                # IAC DONT
                if data == b'\xfe':
                    data = await reader.read(1)
                    self.output(f"IAC DONT {data}")
                                   
                # IAC WILL
                elif data == b'\xfb':
                    data = await reader.read(1)
                    if ord(data) in self.options:
                        self.options[ord(data)].will()
                    else:
                        self.output(f"IAC WILL {ord(data)}")
                
                # IAC WONT
                elif data == b'\xfc':
                    data = await reader.read(1)
                    self.output(f"IAC WONT {data}")

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
                        self.output(f"IAC SB {buf}")

                # TTYPE
                elif data == b'\x18':
                    self.output(f"IAC TTYPE")

                # NAWS
                elif data == b'\x1f':
                    self.output(f"IAC NAWS")

                elif data == b'\xf9':
                    self.output(self.outb.decode("UTF-8", errors="ignore"))
                    self.output("")
                    self.outb = b''

                # IAC UNKNOWN
                else:
                    self.output(f"IAC UNKNOWN {ord(data)}")

            # Catch everything else in our buffer        
            else:
                self.outb = self.outb + data

