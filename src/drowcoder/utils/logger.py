import logging
import sys
import os

from typing import Union, Literal


LogLevel = Union[Literal[10, 20, 30, 40, 50], int]

def enable_default_logger(
    level: LogLevel = logging.INFO,
    directory: str = None,
    name: str = None,
    reinit: bool = True
):
    """Set the default logger handler for the package.

    Will set the root handlers to empty list, prevent duplicate handlers added
    by other packages causing duplicate logging messages.
    """
    logger = logging.getLogger(name or __name__)
    
    if any(not isinstance(handler, logging.NullHandler)
           for handler in logger.handlers):
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)5s] %(message)s',
                                  datefmt='%H:%M:%S')

    if directory:
        if os.path.exists(directory) and reinit:
            os.rmdir(directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_handler = logging.FileHandler(os.path.join(directory, 'logging.log'), encoding='utf8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger