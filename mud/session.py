import asyncio
import socket
import time
from mud.options.msdp import MSDP

class Session:
    def __init__(self, **kwargs):
        self.test = "foo"
        self.client = None
        self.outb = b''
        self.writer = None
        self.connected = False

    def register_options(self, handler):
        self.options = {}
        msdp = MSDP(handler, self.writer)
        self.options[msdp.code] = msdp

    def send(self, msg):
        self.writer.write(bytes(msg + "\n", "UTF-8"))

    async def telnet_client(self, handler):
        self.handler = handler
        reader, self.writer = await asyncio.open_connection("kallistimud.com", 4000)
        #reader, self.writer = await asyncio.open_connection("66.8.164.129", 4000)
        self.connected = True
        self.register_options(handler)
        while True:
            data = await reader.read(1)

            if data == b'':
                raise Exception("Lost connection to server.")
            elif data == b'\n':
                handler(self.outb.decode("UTF-8", errors="ignore").replace("\r"," "))
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
                                handler("IAC WILL TTYPE")
                            case b'\x1f':
                                # IAC WON'T NAWS
                                self.writer.write(b'\xff\xfc\x1f')
                                handler("IAC WON'T NAWS")
                            case _:
                                handler(f"IAC DO {ord(data)}")

                # IAC DONT
                if data == b'\xfe':
                    data = await reader.read(1)
                    handler(f"IAC DONT {data}")
                                   
                # IAC WILL
                elif data == b'\xfb':
                    data = await reader.read(1)
                    if ord(data) in self.options:
                        self.options[ord(data)].will()
                    else:
                        handler(f"IAC WILL {ord(data)}")
                
                # IAC WONT
                elif data == b'\xfc':
                    data = await reader.read(1)
                    handler(f"IAC WONT {data}")

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
                        handler(f"IAC SB {buf}")

                # TTYPE
                elif data == b'\x18':
                    handler(f"IAC TTYPE")

                # NAWS
                elif data == b'\x1f':
                    handler(f"IAC NAWS")

                elif data == b'\xf9':
                    handler(self.outb.decode("UTF-8", errors="ignore"))
                    handler("")
                    self.outb = b''

                # IAC UNKNOWN
                else:
                    handler(f"IAC UNKNOWN {ord(data)}")

            # Catch everything else in our buffer        
            else:
                self.outb = self.outb + data

