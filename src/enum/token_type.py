from enum import Enum, auto

class TokenType(Enum):
    ID = auto()
    INT = auto()
    KEYWORD = auto()
    OP_ARIT = auto()
    OP_REL = auto()
    OP_LOGICO = auto()
    ASSIGN = auto()
    DELIM = auto()
    EOF = auto()
    ERROR = auto()
    