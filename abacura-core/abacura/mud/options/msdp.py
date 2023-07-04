"""MSDP telnet option processor"""
from dataclasses import dataclass
import re
from typing import Any

from textual import log

from abacura.mud.options import IAC, SE, SB, TelnetOption
from abacura.plugins.events import AbacuraMessage

VAR = b'\x01'
VAL = b'\x02'
TABLE_OPEN = b'\x03'
TABLE_CLOSE= b'\x04'
ARRAY_OPEN = b'\x05'
ARRAY_CLOSE= b'\x06'

#TODO: Move ansi_escape somewhere else, we'll need it for triggers
ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

@dataclass
class MSDPMessage(AbacuraMessage):
    """
    MSDP event message
    :param event_type: defaults to core.msdp
    :param subtype: specific MSDP variable changed
    :param value: the new value of the MSDP variable
    :param oldvalue: the original value of the MSDP variable
    """
    event_type:str = "core.msdp"
    subtype: str = ""
    value: str = ""
    oldvalue: str = ""


# TODO all these need to use the regular socket to trap send instead of calling writer directly
class MSDP(TelnetOption):
    """Handle MSDP TelnetOptions"""

    def __init__(self, handler, writer, session):
        self.code = 69
        self.hexcode = b'\x45'
        self.handler = handler
        self.writer = writer
        self.session = session
        self.values = {}
        self.initialized: bool = False

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
                #try:
                #    member[pair[0].decode("UTF-8")] = int(pair[1])
                #except ValueError:
                member[pair[0].decode("UTF-8")] = ansi_escape.sub('',pair[1].decode("UTF-8"))

            return member

        # Empty group
        if buf == b'':
            return []

        buf = buf[3:-2]
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

        items = buf.split(b'\x01')

        exits = {}
        for item in items:
            pair = item.split(b'\x02')
            #try:
            #    exits[pair[0].decode("UTF-8")] = int(pair[1])
            #except ValueError:
            exits[pair[0].decode("UTF-8")] = ansi_escape.sub('',pair[1].decode("UTF-8"))

        return exits

    def request_all_values(self) -> None:
        """Automatically request all possible MSDP values"""
        buf = IAC + SB + self.hexcode + VAR + bytes("REPORT", "UTF-8") + VAL
        msdp_vals = [VAL + bytes(f, "UTF-8") for f in self.values["REPORTABLE_VARIABLES"]]
        buf += VAL.join(msdp_vals) + IAC + SE
        self.writer(buf, raw=True)

    def will(self):
        self.writer(b"\xff\xfd\x45", raw=True)
        response = [IAC,SB,self.hexcode,VAR,b"LIST",VAL,b"REPORTABLE_VARIABLES",IAC,SE]
        self.writer(b''.join(response), raw=True)

    def sb(self, sb):
        log.debug("MSDP SB parsing")
        sb = sb[1:]
        first = sb[0:1]
        if first == b'\x01':
            varname, sb = self.msdpvar(sb)
            var = varname.decode("UTF-8")
            value, sb = self.msdpval(sb)
            try:
                oldvalue = self.values[var]
            except KeyError:
                oldvalue = None

            if var == "REPORTABLE_VARIABLES":
                #self.handler(f"MSDP: Requesting all variables from {var}")
                self.values[var] = self.parse_reportable_variables(value)
                if not self.initialized:
                    self.request_all_values()
                    self.initialized = True
            elif var == "GROUP":
                self.values[var] = self.parse_group(value)
            elif var == "REMORT_LEVELS":
                self.values[var] = self.parse_group(value)
            elif var == "ROOM_EXITS":
                self.values[var] = self.parse_exits(value)
            elif var == "AFFECTS":
                self.values[var] = self.parse_exits(value)
            else:
                self.values[var] = ansi_escape.sub('',value.decode("UTF-8"))
                #try:
                #    self.values[var] = int(self.values[var])
                #except ValueError:
                #    pass

            # Two dispatchers here, first is for all-value listeners
            msg = MSDPMessage(subtype=var, value=self.values[var], oldvalue="")
            self.session.dispatcher(msg)
            # Second dispatch for variable-specific listeners
            msg.event_type = f"core.msdp.{var}"
            self.session.dispatcher(msg)

        else:
            # TODO this is a candidate for some kind of protocol.log
            self.handler(f"MSDP: Don't know how to handle {sb}")
