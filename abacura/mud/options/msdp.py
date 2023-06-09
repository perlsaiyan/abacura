from abacura.mud.options import *
import re
from textual import log
import time

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

    def msdpvar(self, buf):
        buf = buf[1:]
        vn, trash, remainder = buf.partition(VAL)
        return vn, remainder

    def msdpval(self, buf) -> tuple[bytes, bytes]:
        val, trash, remainder = buf.partition(IAC)
        return val, remainder

    # TODO generic handler for MSDP needed
    def msdparray(self, buf):
        pass 
    def msdptable(self, buf):
        pass

    def parse_reportable_variables(self, buf) -> list:
        buf = buf[1:-1]
        list = [x.decode("UTF-8") for x in buf.split(VAL) if len(x) > 1]
        return list

    def parse_group(self, buf) -> list:

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

        list = []
        for element in elements:
            log(f"Parsing {element}")
            list.append(parse_group_member(element))
        
        log(list)
        return list
        
        


    def request_all_values(self) -> None:
        for x in self.values["REPORTABLE_VARIABLES"]:
            # self.handler(f"Requesting MSDP value {x}")
            # without this sleep, I'm not getting GROUP?
            time.sleep(0.001)
            self.writer.write(b''.join(
                [IAC, SB, self.hexcode,
                 VAR, bytes("REPORT", "UTF-8"), 
                 VAL, bytes(x, "UTF-8"), 
                 IAC, SE]
                ))
            
    def will(self):
        self.writer.write(b"\xff\xfd\x45")
        response = [IAC,SB,self.hexcode,VAR,b"LIST",VAL,b"REPORTABLE_VARIABLES",IAC,SE]
        self.writer.write(b''.join(response))
    
    # MSDP subnegotiation parser
    def sb(self, sb):
        log("MSDP SB parsing")
        sb = sb[1:]
        ch = sb[0:1]
        if ch == b'\x01':
            varname, sb = self.msdpvar(sb)
            var = varname.decode("UTF-8")
            value, sb = self.msdpval(sb)

            if var == "REPORTABLE_VARIABLES":
                #self.handler(f"MSDP: Requesting all variables from {var}")
                self.values[var] = self.parse_reportable_variables(value)
                self.request_all_values()
            elif var == "GROUP":
                self.values[var] = self.parse_group(value)
            else:
                self.values[var] = ansi_escape.sub('',value.decode("UTF-8"))
                try:
                    self.values[var] = int(self.values[var])
                except ValueError:
                    pass
                        
        else:
            self.handler(f"MSDP: Don't know how to handle {sb}")
