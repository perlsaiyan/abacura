from .default import TelnetOption, SB, DO, DONT, WILL, WONT, IAC, SE

VAR = b'\x01'
VAL = b'\x02'
TABLE_OPEN = b'\x03'
TABLE_CLOSE= b'\x04'
ARRAY_OPEN = b'\x05'
ARRAY_CLOSE= b'\x06'

class MSDP(TelnetOption):
    def __init__(self, handler, writer):
        self.code = 69
        self.hexcode = b'\x45'
        self.handler = handler
        self.writer = writer
    
    def will(self):
        self.writer.write(b"\xff\xfd\x45")
        response = [IAC,SB,self.hexcode,VAR,b"LIST",VAL,b"REPORTABLE_VARIABLES",IAC,SE]
        self.writer.write(b''.join(response))
    
    def sb(self, sb):
        self.handler(f"GOT MSDP SB - {sb}")
