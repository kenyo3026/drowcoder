import json
import pathlib
import platform
import shutil
import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

_SENTINEL = object()

class CheckpointError(Exception):
    pass

@dataclass(frozen=True)
class TxtPunchMode:
    append: str = 'a'
    write: str = 'w'

    @classmethod
    def check(cls, val: Any, default: Any = _SENTINEL):
        for group in cls.__dict__.items():
            if val in group:
                return group[1]
        if default is not _SENTINEL:
            return default
        raise CheckpointError(f"Key '{val}' not found.")

    @classmethod
    def get_mode_name(cls, val: Any, default: Any = _SENTINEL):
        for key, value in cls.__dict__.items():
            if val == value:
                return key
        if default is not _SENTINEL:
            return default
        raise CheckpointError(f"Value '{val}' not found.")

@dataclass
class CheckpointTxtBase:
    path: str
    context: Optional[str] = None

    def __post_init__(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(self.context or '')

    def punch(self, context: str, mode: Union[str, TxtPunchMode]='a'):
        mode = TxtPunchMode.check(mode)
        mode_name = TxtPunchMode.get_mode_name(mode)

        pathlib.Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        try:
            if context is None:
                context = ""
            with open(self.path, mode, encoding='utf-8') as f:
                f.write(context)
        except Exception as e:
            raise CheckpointError(f"Failed to {mode_name} {self.path}: {e}")

@dataclass
class CheckpointDictBase:
    path: str
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.dump()

    def punch(self, context: Dict[str, Any]):
        self.context.update(context)
        self.dump()

    def dump(self):
        pass

@dataclass
class CheckpointListBase:
    path: str
    context: List[Any] = field(default_factory=list)

    def __post_init__(self):
        self.dump()

    def punch(self, context: Any):
        self.context.append(context)
        self.dump()

    def dump(self):
        pass

@dataclass
class CheckpointJsonBase:
    def __new__(cls, path: str, context: Union[Dict[str, Any], List[Any]] = None):
        if context is None:
            context = []

        if isinstance(context, dict):
            instance = CheckpointDictBase(path, context)
            instance.dump = lambda: cls._dump_json(instance)
            return instance
        elif isinstance(context, list):
            instance = CheckpointListBase(path, context)
            instance.dump = lambda: cls._dump_json(instance)
            return instance
        else:
            raise ValueError(f"Unsupported context type: {type(context)}")

    @staticmethod
    def _dump_json(instance):
        pathlib.Path(instance.path).parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(instance.path, 'w', encoding='utf-8') as f:
                json.dump(instance.context, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise CheckpointError(f"Failed to write {instance.path}: {e}")

@dataclass
class CheckpointInfo:
    def __new__(cls, path: str, context: Dict[str, Any] = None):
        _base_context = {
            'create_datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **platform.uname()._asdict()
        }
        context = {**_base_context, **(context or {})}
        return CheckpointJsonBase(path, context)

@dataclass
class CheckpointConfig:
    def __new__(cls, path: str, context: Union[Dict[str, Any], List[Any]] = None):
        return CheckpointJsonBase(path, context)

@dataclass
class CheckpointLogs:
    def __new__(cls, path: str, context: Union[Dict[str, Any], List[Any]] = None):
        return CheckpointTxtBase(path, context)

@dataclass
class CheckpointMessages:
    def __new__(cls, path: str, context: Union[Dict[str, Any], List[Any]] = None):
        return CheckpointJsonBase(path, context)

@dataclass
class CheckpointRawMessages:
    def __new__(cls, path: str, context: Union[Dict[str, Any], List[Any]] = None):
        return CheckpointJsonBase(path, context)

class Checkpoint:

    def __init__(
        self,
        root:str=None,
        force_reinit_if_existence:bool=True,
        logger=None,
    ):
        self.logger = logger
        self.init_checkpoint(root, force_reinit_if_existence)

        self.info = CheckpointInfo(
            path = self.checkpoint_root / 'info.json',
        )

        self.config = CheckpointConfig(
            path = self.checkpoint_root / 'config.json',
        )

        self.logs = CheckpointLogs(
            path = self.checkpoint_root / 'logging.log',
        )

        self.messages = CheckpointMessages(
            path = self.checkpoint_root / 'messages.json',
        )

        self.raw_messages = CheckpointRawMessages(
            path = self.checkpoint_root / 'raw_messages.json',
        )

    def init_checkpoint(self, root:str=None, force_reinit_if_existence:bool=True):
        if not root:
            root = f'checkpoint_{datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}'
        self.checkpoint_root = pathlib.Path(root)

        if force_reinit_if_existence:
            if self.checkpoint_root.exists():
                if self.logger:
                    self.logger.info(f"Remove existing directory: {self.checkpoint_root}")
                try:
                    shutil.rmtree(self.checkpoint_root)
                except OSError as e:
                    if self.logger:
                        self.logger.error(f"Error removing directory: {e}")

        if self.logger:
            self.logger.info(f"Create checkpoint directory: {self.checkpoint_root}")
        self.checkpoint_root.mkdir(parents=True, exist_ok=True)

    def punch_info(self, *args, **kwargs):
        self.info.punch(*args, **kwargs)

    def punch_log(self, *args, **kwargs):
        self.logs.punch(*args, **kwargs)

    def punch_message(self, *args, **kwargs):
        self.messages.punch(*args, **kwargs)

    def punch_raw_message(self, *args, **kwargs):
        self.raw_messages.punch(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.punch_log(f"Error occurred: {exc_val}")

if __name__ == "__main__":
    checkpoint = Checkpoint(root='../checkpoint/test')