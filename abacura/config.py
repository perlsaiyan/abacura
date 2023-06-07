from pathlib import Path
from tomlkit import parse

class Config():
    _config = None
    _config_file: str
       
    def __init__(self, **kwargs):
        if "config" not in kwargs or kwargs["config"] is None:
            kwargs["config"] = "~/.abacura"
        self._config_file = kwargs["config"]
        self.reload()

    def reload(self) -> None:
        cfile = Path(self._config_file).expanduser()
        self._config = parse(open(cfile,"r").read())
    
    @property
    def config(self):
        return self._config