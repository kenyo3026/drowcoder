import logging
import sys
import os
import pathlib
from typing import Union, Literal, Optional
from rich.logging import RichHandler


LogLevel = Union[Literal[10, 20, 30, 40, 50], int]


class DefaultLogger:
    """Default logger with file and stream handlers."""

    def __init__(
        self,
        level     : LogLevel = logging.INFO,
        directory : Union[str, pathlib.Path] = None,
        name      : Optional[str] = None,
        reinit    : bool = True,
        file_open_mode : str = 'a',
    ):
        self.level = level
        self.directory = pathlib.Path(directory)
        self.name = name
        self.reinit = reinit
        self.file_open_mode = 'w' if reinit else file_open_mode

    def setup(self) -> logging.Logger:
        """Setup logger with default configuration."""
        # Create directory if needed
        if self.directory and not os.path.exists(self.directory):
            os.makedirs(self.directory)

        logger = logging.getLogger(self.name or __name__)

        # Skip if already configured and reinit=False
        if not self.reinit and logger.handlers:
            return logger

        # Clear existing handlers if reinit=True
        if self.reinit:
            logger.handlers.clear()

        logger.setLevel(self.level)

        # Add handlers
        self.add_handlers(logger)

        return logger

    def add_handlers(self, logger: logging.Logger) -> None:
        """Add default handlers."""
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)5s] %(message)s',
            datefmt='%H:%M:%S'
        )

        # Add file handler
        if self.directory:
            file_handler = logging.FileHandler(
                self.directory / 'logging.log',
                mode=self.file_open_mode,
                encoding='utf8',
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Add stream handler
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)


class RichLogger(DefaultLogger):
    """Rich logger that extends default logger with RichHandler."""

    def __init__(
        self,
        level     : LogLevel = logging.INFO,
        directory : Union[str, pathlib.Path] = None,
        name      : Optional[str] = None,
        reinit    : bool = True,
        file_open_mode  : str = 'a',
        rich_tracebacks : bool = True,
    ):
        super().__init__(level, directory, name, reinit, file_open_mode)
        self.rich_tracebacks = rich_tracebacks

    def add_handlers(self, logger: logging.Logger) -> None:
        """Add rich console handler and file handler."""
        # Add rich console handler (replaces stream handler)
        rich_handler = RichHandler(rich_tracebacks=self.rich_tracebacks)
        logger.addHandler(rich_handler)

        # Add file handler (same as parent)
        if self.directory:
            formatter = logging.Formatter(
                fmt='%(asctime)s [%(levelname)5s] %(message)s',
                datefmt='%H:%M:%S'
            )
            file_handler = logging.FileHandler(
                self.directory / 'logging.log',
                mode=self.file_open_mode,
                encoding='utf8',
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)


def enable_default_logger(
    level     : LogLevel = logging.INFO,
    directory : Union[str, pathlib.Path] = None,
    name      : Optional[str] = None,
    reinit    : bool = True,
    file_open_mode : str = 'a',
) -> logging.Logger:
    """Create default logger."""
    return DefaultLogger(level, directory, name, reinit, file_open_mode).setup()


def enable_rich_logger(
    level     : LogLevel = logging.INFO,
    directory : Union[str, pathlib.Path] = None,
    name      : Optional[str] = None,
    reinit    : bool = True,
    file_open_mode  : str = 'a',
    rich_tracebacks : bool = True,
) -> logging.Logger:
    """Create rich logger."""
    return RichLogger(level, directory, name, reinit, file_open_mode, rich_tracebacks).setup()
