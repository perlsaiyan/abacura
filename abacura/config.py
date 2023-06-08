from pathlib import Path
from tomlkit import parse

class Config():
    _config = None
    _config_file: str
       
    def __init__(self, **kwargs):
        if "config" not in kwargs or kwargs["config"] is None:
            kwargs["config"] = "~/.abacura"
            p = Path(kwargs["config"]).expanduser()
            if not p.is_file():
                with open(p, "w"):
                    pass
        self._config_file = kwargs["config"]
        self.reload()

    def reload(self) -> None:
        cfile = Path(self._config_file).expanduser()
        try:
            self._config = parse(open(cfile,"r").read())
        except Exception as e:
            print(f"{cfile}: {repr(e)}")
            exit(1)
    
    @property
    def config(self):
        return self._config