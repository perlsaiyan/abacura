SB = b'\xfa'
SE = b'\xf0'
WILL = b'\xfb'
WONT = b'\xfc'
DO = b'\xfd'
DONT = b'\xfe'
IAC = b'\xff'


class TelnetOption():
    def __init__(self, code: int):
        pass

    def do(self):
        pass

    def dont(self):
        pass

    def will(self):
        pass

    def wont(self):
        pass

    def sb(self, sb):
        pass