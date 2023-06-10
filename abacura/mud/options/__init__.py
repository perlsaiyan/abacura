"""Telnet Options handler module"""
SB = b'\xfa'
SE = b'\xf0'
WILL = b'\xfb'
WONT = b'\xfc'
DO = b'\xfd'
DONT = b'\xfe'
IAC = b'\xff'

class TelnetOption():
    """Base class for Telnet Option handling"""
    def __init__(self, code: int):
        pass

    def do(self) -> None:
        """IAC DO handler"""

    def dont(self) -> None:
        """IAC DONT handler"""

    def will(self) -> None:
        """IAC WILL handler"""

    def wont(self) -> None:
        """IAC WONT handler"""

    def sb(self, sb):
        """IAC SB handler"""
