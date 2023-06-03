from .default import TelnetOption, SB, DO, DONT, WILL, WONT, IAC, SE
import time

VAR = b'\x01'
VAL = b'\x02'
TABLE_OPEN = b'\x03'
TABLE_CLOSE= b'\x04'
ARRAY_OPEN = b'\x05'
ARRAY_CLOSE= b'\x06'

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

    def request_all_values(self) -> None:
        for x in self.values["REPORTABLE_VARIABLES"]:
            # self.handler(f"Requesting MSDP value {x}")
            # without this sleep, I'm not getting GROUP?
            time.sleep(0.0005)
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
    
    # TODO parse MSDP subnegotiations
    def sb(self, sb):
        sb = sb[1:]
        # TODO MSDP Subnegotiation Buffer
        match sb[0:1]:
            case b'\x01':
                varname, sb = self.msdpvar(sb)
                var = varname.decode("UTF-8")
                value, sb = self.msdpval(sb)

                match var:
                    case "REPORTABLE_VARIABLES":
                        #self.handler(f"MSDP: Requesting all variables from {var}")
                        self.values[var] = self.parse_reportable_variables(value)
                        self.request_all_values()
                    case other:
                        
                        self.values[var] = value.decode("UTF-8")          
                        try: 
                            self.values[var] = int(self.values[var])
                        except ValueError:
                            pass
                        
            case _:
                self.handler(f"MSDP: Don't know how to handle {sb}")

        #self.handler(f"GOT MSDP SB - {sb}")
