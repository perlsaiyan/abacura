"""
Logging module for sessions
"""

from datetime import datetime
import logging
from pathlib import Path
from rich.text import Text

from abacura import Config

class LOKLogger:

    def __init__(self, name: str, config: Config):
        if config.get_specific_option(name, "log_dir"):
            logfile = Path(config.get_specific_option(name, "log_dir")).expanduser()
            self.logfile = logfile.joinpath(datetime.now().strftime(config.get_specific_option(name, "log_file")))
        else:
            self.logfile = None

        if self.logfile:
            logging.basicConfig(
                filename=self.logfile,
                filemode="a",
                level=logging.DEBUG
            )
            self.logger = logging.getLogger("abacura-kallisti")
        else:
            self.logger = None

    def info(self, msg, **kwargs):
        if self.logger:
            self.logger.info(msg, *kwargs)
       
    def warn(self, msg, **kwargs):
        if self.logger:
            self.logger.warning(msg, *kwargs)

    def error(self, msg, **kwargs):
        if self.logger:
            self.logger.error(msg, *kwargs)

