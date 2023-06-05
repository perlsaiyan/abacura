from pathlib import Path
from tomlkit import parse

class Config():
    config = None

    def __init__(self, **kwargs):
        if "config" not in kwargs or kwargs["config"] is None:
            kwargs["config"] = "~/.abacura"
        
        cfile = Path(kwargs["config"]).expanduser()
        
        self.config = parse(open(cfile,"r").read())

    
