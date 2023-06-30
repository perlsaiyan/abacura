"""Abacura configuration module"""

import os
from pathlib import Path
from typing import Any

from tomlkit import parse, TOMLDocument

DEFAULT_GLOBAL_CONFIG = {
    "module_paths": [],
    "css_path": os.path.join(os.path.dirname(__file__),"css/abacura.css"),
    "ga": True
}


class Config:
    """Base configuration class"""
    _config_file: str
    name = "config"
       
    def __init__(self, **kwargs):
        super().__init__()
        if "config" not in kwargs or kwargs["config"] is None:
            kwargs["config"] = "~/.abacura"
            p = Path(kwargs["config"]).expanduser()
            if not p.is_file():
                with open(p, "w", encoding="UTF-8"):
                    pass
        self._config_file = kwargs["config"]
        self.reload()

    def reload(self) -> None:
        """Reload configuration file from disk"""
        cfile = Path(self._config_file).expanduser()
        try:
            self._config = parse(open(cfile, "r", encoding="UTF-8").read())

        except Exception as config_exception:
            raise (config_exception)

    def get_specific_option(self, section: str, key: str, default=None) -> Any:
        """Get configuration value for section, global, or default"""

        if section in self.config and key in self.config[section]:
            return self.config[section][key]

        if "global" in self.config and key in self.config["global"]:
            return self.config["global"][key]

        if key in DEFAULT_GLOBAL_CONFIG:
            return DEFAULT_GLOBAL_CONFIG[key]

        return default

    def data_directory(self, section: str) -> Path:
        """Returns the per-session repository of save files for persistence"""
        if section in self.config and "data_directory" in self.config[section]:
            path = Path(os.path.join(self.config[section]["data_directory"], section)).expanduser()
        else:
            path = Path(os.path.join("~/Documents/abacura", section)).expanduser()

        path.mkdir(parents=True, exist_ok=True)
        return path

    def ring_log(self, section: str) -> str:
        """Returns the location of the ring log"""
        return Path(os.path.join(self.data_directory(section), "ringlog.db")).as_posix()
    
    @property
    def config(self) -> TOMLDocument:
        return self._config
