from dataclasses import dataclass

from .coder import INSTRUCTION_FOR_CODER


@dataclass(frozen=True)
class InstructionType:
    EMPTY :str = 'EMPTY'
    CODER :str = 'CODER'

@dataclass(frozen=True)
class InstructionFactory:
    EMPTY :str = f''
    CODER :str = INSTRUCTION_FOR_CODER