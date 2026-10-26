import logging
import sys
from typing import ClassVar


def setup_local_logging():
    # Get root logger
    logger = logging.getLogger()

    # Add stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(ColorLogFormatter())
    logger.addHandler(stdout_handler)


class ColorLogFormatter(logging.Formatter):
    blue = "\033[36;20m"
    grey = "\033[38;20m"
    red = "\033[31;20m"
    yellow = "\033[33;20m"
    bold = "\033[1m"
    reset = "\033[0m"

    log_format = "%(asctime)s [%(levelname)s]: %(message)s (%(name)s)"

    color_map: ClassVar[dict[int, str]] = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: blue + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: red + bold + log_format + reset,
    }

    def format(self, record):
        log_format = self.color_map.get(record.levelno)
        formatter = logging.Formatter(log_format, datefmt="%m/%d/%Y %I:%M:%S %p")
        return formatter.format(record)
