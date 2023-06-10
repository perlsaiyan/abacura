"""MSDP telnet option processor"""
import re
import time

from textual import log

from abacura.mud.options import IAC, SE, SB, TelnetOption

VAR = b'\x01'
VAL = b'\x02'
TABLE_OPEN = b'\x03'
TABLE_CLOSE= b'\x04'
ARRAY_OPEN = b'\x05'
ARRAY_CLOSE= b'\x06'

#TODO: Move ansi_escape somewhere else, we'll need it for triggers
ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class MSDP(TelnetOption):
    """Handle MSDP TelnetOptions"""

    def __init__(self, handler, writer):
        self.code = 69
        self.hexcode = b'\x45'
        self.handler = handler
        self.writer = writer
        self.values = {}

    def msdpvar(self, buf) -> tuple[bytes, bytes]:
        """Handle MSDP VAR sequences"""
        buf = buf[1:]
        name, _, remainder = buf.partition(VAL)
        return name, remainder

    def msdpval(self, buf) -> tuple[bytes, bytes]:
        """Handle MSDP VAL sequences"""
        val, _, remainder = buf.partition(IAC)
        return val, remainder

    # TODO generic handler for MSDP array and tables needed
    def msdparray(self, buf):
        """NotImplemented: generic MSDP array parser"""

    def msdptable(self, buf):
        """NotImplemented: generic MSDP table parser"""

    # TODO move this to abacura-kallisti once we have config options for MSDP parser
    def parse_reportable_variables(self, buf) -> list:
        """Kallisti-specific parser for REPORTABLE_VARIABLES"""
        buf = buf[1:-1]
        return [x.decode("UTF-8") for x in buf.split(VAL) if len(x) > 1]

    def parse_group(self, buf) -> list:
        """Kallisti-specifc parser for GROUP"""

        def parse_group_member(line) -> dict:
            items = line.split(b'\x01')
            member = {}
            items = items[1:]
            for item in items:
                pair = item.split(b'\x02')
                log(f"Found pair {pair}")
                try:
                    member[pair[0].decode("UTF-8")] = int(pair[1])
                except ValueError:
                    member[pair[0].decode("UTF-8")] = ansi_escape.sub('',pair[1].decode("UTF-8"))

            return member

        # Empty group
        if buf == b'':
            return []

        log(f"Start group parse with {buf}")
        buf = buf[3:-2]
        log(f"Stripped group parse to {buf}")
        elements = buf.split(b'\x04\x02\x03')

        log(elements)

        element_list = []
        for element in elements:
            log(f"Parsing {element}")
            element_list.append(parse_group_member(element))

        log(element_list)
        return element_list

    def parse_exits(self, buf) -> dict:
        """Kallisti-specific parser for ROOM_EXITS"""
        if buf == b'':
            return {}

        buf = buf[2:-1]
        log(f"parse exits {buf}")

        items = buf.split(b'\x01')
        log(f"items {items}")

        exits = {}
        for item in items:
            pair = item.split(b'\x02')
            log(f"Found pair {pair}")
            try:
                exits[pair[0].decode("UTF-8")] = int(pair[1])
            except ValueError:
                exits[pair[0].decode("UTF-8")] = ansi_escape.sub('',pair[1].decode("UTF-8"))

        return exits

    def request_all_values(self) -> None:
        """Automatically request all possible MSDP values"""
        for key in self.values["REPORTABLE_VARIABLES"]:
            log(f"Requesting MSDP value {key}")
            # tiny sleep to avoid overwriting socket
            # TODO see why this is possible, in Session?
            time.sleep(0.001)
            self.writer.write(b''.join(
                [IAC, SB, self.hexcode,
                 VAR, bytes("REPORT", "UTF-8"),
                 VAL, bytes(key, "UTF-8"),
                 IAC, SE]
                ))

    def will(self):
        self.writer.write(b"\xff\xfd\x45")
        response = [IAC,SB,self.hexcode,VAR,b"LIST",VAL,b"REPORTABLE_VARIABLES",IAC,SE]
        self.writer.write(b''.join(response))

    def sb(self, sb):
        log("MSDP SB parsing")
        sb = sb[1:]
        first = sb[0:1]
        if first == b'\x01':
            varname, sb = self.msdpvar(sb)
            var = varname.decode("UTF-8")
            value, sb = self.msdpval(sb)

            if var == "REPORTABLE_VARIABLES":
                #self.handler(f"MSDP: Requesting all variables from {var}")
                self.values[var] = self.parse_reportable_variables(value)
                self.request_all_values()
            elif var == "GROUP":
                self.values[var] = self.parse_group(value)
            elif var == "ROOM_EXITS":
                self.values[var] = self.parse_exits(value)
            else:
                self.values[var] = ansi_escape.sub('',value.decode("UTF-8"))
                try:
                    self.values[var] = int(self.values[var])
                except ValueError:
                    pass

        else:
            # TODO this is a candidate for some kind of protocol.log
            self.handler(f"MSDP: Don't know how to handle {sb}")
