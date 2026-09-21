from src.classes.token import Token, TokenType
import sys

class Scanner:
    KEYWORDS = {
        "programa", "var", "inteiro", "booleano", "se", "senão",
        "enquanto", "escreva", "leia", "verdadeiro", "falso",
        "e", "ou", "não", "fim"
    }

    def __init__(self, source_code: str):
        self.source = source_code
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.source[self.pos] if self.source else None

    def advance(self):
        """Avança o ponteiro de leitura para o próximo caractere e atualiza a posição."""
        if self.current_char == '\n':
            self.line += 1
            self.col = 0
        
        self.pos += 1
        self.col += 1
        self.current_char = self.source[self.pos] if self.pos < len(self.source) else None

    def peek(self) -> str | None:
        peek_pos = self.pos + 1
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None

    def get_next_token(self) -> Token:
        """Processa a cadeia de caracteres e retorna o próximo token válido."""
        while self.current_char is not None:            
            if self.current_char.isspace():
                self.advance()
                continue
            
            if self.current_char == '#':
                while self.current_char is not None and self.current_char != '\n':
                    self.advance()
                continue

            if self.current_char.isalpha():
                start_col = self.col
                result = ""
                while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
                    result += self.current_char
                    self.advance()
                
                if result in self.KEYWORDS:
                    if result in {"e", "ou", "não"}:
                        return Token(TokenType.OP_LOGICO, result, self.line, start_col)
                    return Token(TokenType.KEYWORD, result, self.line, start_col)
                
                return Token(TokenType.ID, result, self.line, start_col)

            # Números Inteiros
            if self.current_char.isdigit():
                start_col = self.col
                result = ""
                while self.current_char is not None and self.current_char.isdigit():
                    result += self.current_char
                    self.advance()
                return Token(TokenType.INT, result, self.line, start_col)

            # Operadores Relacionais e de Atribuição
            char = self.current_char
            start_col = self.col

            if char in {'=', '<', '>', '!'}:
                next_char = self.peek()
                
                if next_char == '=':
                    self.advance() # Consome o caractere atual ('=', '<', '>', ou '!')
                    self.advance() # Consome o '=' do lookahead
                    return Token(TokenType.OP_REL, char + '=', self.line, start_col)
                
                elif char == '=':
                    self.advance()
                    return Token(TokenType.ASSIGN, '=', self.line, start_col)
                
                elif char == '!':
                    error_msg = f"Erro Léxico: Caractere inesperado '!' na linha {self.line}, coluna {start_col}"
                    print(error_msg, file=sys.stderr)
                    self.advance()
                    return Token(TokenType.ERROR, "!", self.line, start_col)
                
                else:
                    self.advance()
                    return Token(TokenType.OP_REL, char, self.line, start_col)

            # Operadores Aritméticos
            if char in {'+', '-', '*', '/', '%'}:
                self.advance()
                return Token(TokenType.OP_ARIT, char, self.line, start_col)

            # Delimitadores
            if char in {'(', ')', '{', '}', ';', ':', ',', '.'}:
                self.advance()
                return Token(TokenType.DELIM, char, self.line, start_col)

            # Tratamento de caracteres desconhecidos
            error_msg = f"Erro Léxico: Caractere inválido '{char}' na linha {self.line}, coluna {start_col}"
            print(error_msg, file=sys.stderr)
            invalid_char = char
            self.advance()
            return Token(TokenType.ERROR, invalid_char, self.line, start_col)

        return Token(TokenType.EOF, "", self.line, self.col)