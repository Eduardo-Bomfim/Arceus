from dataclasses import dataclass
from src.enum.token_type import TokenType

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self):
        return f"Token(type={self.type}, value='{self.value}', line={self.line}, column={self.column})"