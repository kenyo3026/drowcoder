import logging
import pathlib
from typing import Callable, Optional, Union, TypedDict


class ToolRuntimeDict(TypedDict, total=False):
    """
    Dictionary type that matches ToolRuntime attributes.

    All fields are optional (total=False) to match ToolRuntime's default values.
    """
    logger: Optional[logging.Logger]
    callback: Optional[Callable]
    checkpoint: Optional[Union[str, pathlib.Path]]
