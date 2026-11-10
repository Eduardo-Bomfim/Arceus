from enum import Enum, auto

class DataType(Enum):
    INTEIRO = auto()
    BOOLEANO = auto()
    ERROR = auto()  # Sentinela para evitar cascata de erros semânticos
