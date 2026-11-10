from __future__ import annotations
import sys
from src.classes.ast_nodes import (
    AssignNode,
    AstNode,
    BinOpNode,
    BlockNode,
    ExprNode,
    ForNode,
    IfNode,
    LiteralNode,
    ProgramNode,
    ReadNode,
    RepeatNode,
    UnaryOpNode,
    VarDeclNode,
    VarNode,
    WhileNode,
    WriteNode,
)
from src.classes.scanner import Scanner
from src.classes.token import Token
from src.enum.data_type import DataType
from src.enum.token_type import TokenType

class _ParseSyncError(Exception):
    """Exceção interna usada para acionar a recuperação em modo pânico."""

class Parser:
    """Analisador Sintático Descendente Recursivo LL(1) para MiniLang."""

    SYNC_KEYWORDS = {
        "var",
        "se",
        "enquanto",
        "escreva",
        "leia",
        "para",
        "repita",
        "fim",
    }

    BLOCK_BODY_STARTERS = {
        "var",
        "se",
        "enquanto",
        "escreva",
        "leia",
        "para",
        "repita",
    }

    def __init__(self, scanner: Scanner, emit_errors: bool = True):
        self.scanner = scanner
        self.emit_errors = emit_errors
        self.errors: list[str] = []
        self.had_lexical_error: bool = False
        self._token_index: int = 0
        self.current_token: Token = self._next_valid_token()

    def _next_valid_token(self) -> Token:
        """Obtém o próximo token do Scanner ignorando tokens TokenType.ERROR."""
        while True:
            token = self.scanner.get_next_token()
            if token.type == TokenType.ERROR:
                self.had_lexical_error = True
                continue
            return token

    def _advance(self) -> Token:
        previous = self.current_token
        if previous.type != TokenType.EOF:
            self.current_token = self._next_valid_token()
            self._token_index += 1
        return previous

    def _is_at_end(self) -> bool:
        return self.current_token.type == TokenType.EOF

    def _check(self, token_type: TokenType) -> bool:
        return self.current_token.type == token_type

    def _check_keyword(self, keyword: str) -> bool:
        return (
            self.current_token.type == TokenType.KEYWORD
            and self.current_token.value == keyword
        )

    def _check_delim(self, delim: str) -> bool:
        return (
            self.current_token.type == TokenType.DELIM
            and self.current_token.value == delim
        )

    def _check_op_logico(self, op: str) -> bool:
        return (
            self.current_token.type == TokenType.OP_LOGICO
            and self.current_token.value == op
        )

    def _match_keyword(self, keyword: str) -> bool:
        if self._check_keyword(keyword):
            self._advance()
            return True
        return False

    def _match_delim(self, delim: str) -> bool:
        if self._check_delim(delim):
            self._advance()
            return True
        return False

    def _match_op_logico(self, op: str) -> Token | None:
        if self._check_op_logico(op):
            return self._advance()
        return None

    def _is_sync_keyword(self, extra_keywords: set[str] | None = None) -> bool:
        if self.current_token.type != TokenType.KEYWORD:
            return False
        if self.current_token.value in self.SYNC_KEYWORDS:
            return True
        return bool(extra_keywords and self.current_token.value in extra_keywords)

    def _is_block_body_starter(self) -> bool:
        return (
            self._check(TokenType.ID)
            or self._check_delim("{")
            or (
                self.current_token.type == TokenType.KEYWORD
                and self.current_token.value in self.BLOCK_BODY_STARTERS
            )
        )

    def _report_expected(self, expected: str, token: Token | None = None) -> None:
        tok = token or self.current_token
        found = "EOF" if tok.type == TokenType.EOF else tok.value
        self._report_raw(f"{expected}, encontrado '{found}'", tok)

    def _report_raw(self, description: str, token: Token | None = None) -> None:
        tok = token or self.current_token
        formatted = f"[Erro Sintático] Linha {tok.line}, Coluna {tok.column}: {description}"
        self.errors.append(formatted)
        if self.emit_errors:
            print(formatted, file=sys.stderr)

    def _expect_keyword(self, keyword: str, error_msg: str) -> Token:
        if self._check_keyword(keyword):
            return self._advance()
        self._report_expected(error_msg)
        raise _ParseSyncError()

    def _expect_delim(self, delim: str, error_msg: str) -> Token:
        if self._check_delim(delim):
            return self._advance()
        self._report_expected(error_msg)
        raise _ParseSyncError()

    def _expect_id(self, error_msg: str) -> Token:
        if self._check(TokenType.ID):
            return self._advance()
        self._report_expected(error_msg)
        raise _ParseSyncError()

    def _expect(self, token_type: TokenType, value: str, error_msg: str) -> Token:
        if (
            self.current_token.type == token_type
            and self.current_token.value == value
        ):
            return self._advance()
        self._report_expected(error_msg)
        raise _ParseSyncError()

    def synchronize(self, extra_keywords: set[str] | None = None) -> None:
        """Modo pânico: descarta tokens até alcançar um ponto de sincronização seguro."""
        while not self._is_at_end():
            if self._check_delim(";"):
                self._advance()
                return
            if self._check_delim("}"):
                return
            if self._is_sync_keyword(extra_keywords):
                return
            self._advance()

    def parse(self) -> ProgramNode | None:
        """Ponto de entrada principal da análise sintática."""
        return self.parse_program()

    def parse_program(self) -> ProgramNode | None:
        """Programa ::= 'programa' ID Bloco 'fim' '.' EOF ;"""
        if self._is_at_end():
            self._report_expected("esperado 'programa'")
            return None

        has_programa = self._check_keyword("programa")
        if has_programa:
            prog_tok = self._advance()
        else:
            prog_tok = self.current_token
            self._report_expected("esperado 'programa'")
            while (
                not self._is_at_end()
                and not self._check(TokenType.ID)
                and not self._check_delim("{")
                and not self._is_sync_keyword()
            ):
                self._advance()
            if self._is_at_end():
                return None

        if self._check(TokenType.ID):
            name_tok = self._advance()
            prog_name = name_tok.value
        else:
            if has_programa:
                self._report_expected("esperado identificador com o nome do programa")
            prog_name = "<desconhecido>"
            while (
                not self._is_at_end()
                and not self._check_delim("{")
                and not self._is_block_body_starter()
                and not self._check_keyword("fim")
            ):
                self._advance()

        if self._check_delim("{"):
            block = self.parse_block(require_open_brace=True)
        else:
            self._report_expected("esperado '{' para iniciar o bloco do programa")
            if self._is_block_body_starter() or self._check_keyword("fim"):
                block = self.parse_block(require_open_brace=False)
            else:
                block = BlockNode(
                    self.current_token.line, self.current_token.column, [], []
                )

        has_fim = self._match_keyword("fim")
        if not has_fim:
            self._report_expected("esperado 'fim'")
            while (
                not self._is_at_end()
                and not self._check_keyword("fim")
                and not self._check_delim(".")
            ):
                self._advance()
            has_fim = self._match_keyword("fim")

        if not self._match_delim("."):
            if has_fim or not self._is_at_end():
                self._report_expected("esperado '.' após 'fim'")

        if not self._is_at_end():
            self._report_expected("esperado fim de arquivo (EOF) após 'fim.'")

        return ProgramNode(prog_tok.line, prog_tok.column, prog_name, block)

    def parse_block(self, require_open_brace: bool = True) -> BlockNode:
        """Bloco ::= '{' { Declaracao } { Comando } '}' ;"""
        if require_open_brace:
            open_tok = self._expect_delim("{", "esperado '{' para iniciar bloco")
            block_line, block_col = open_tok.line, open_tok.column
        else:
            block_line, block_col = (
                self.current_token.line,
                self.current_token.column,
            )

        declarations: list[VarDeclNode] = []
        statements: list[AstNode] = []

        while self._check_keyword("var"):
            start_idx = self._token_index
            try:
                declarations.append(self.parse_var_decl())
            except _ParseSyncError:
                if self._token_index == start_idx and not self._is_at_end():
                    self._advance()
                self.synchronize()

        while (
            not self._check_delim("}")
            and not self._check_keyword("fim")
            and not self._is_at_end()
        ):
            start_idx = self._token_index
            if self._check_keyword("var"):
                self._report_raw(
                    "declaração 'var' deve aparecer antes dos comandos do bloco"
                )
                try:
                    declarations.append(self.parse_var_decl())
                except _ParseSyncError:
                    if self._token_index == start_idx and not self._is_at_end():
                        self._advance()
                    self.synchronize()
                continue

            try:
                statements.append(self.parse_statement())
            except _ParseSyncError:
                if (
                    self._token_index == start_idx
                    and not self._check_delim("}")
                    and not self._check_keyword("fim")
                    and not self._is_at_end()
                ):
                    self._advance()
                self.synchronize()

        if self._check_delim("}"):
            self._advance()
        else:
            self._report_expected("esperado '}' para fechar bloco")

        return BlockNode(block_line, block_col, declarations, statements)

    def parse_var_decl(self) -> VarDeclNode:
        """Declaracao ::= 'var' ID { ',' ID } [ ':' ] Tipo ';' ;"""
        var_tok = self._expect_keyword("var", "esperado 'var'")
        names: list[str] = []

        first_id = self._expect_id("esperado identificador após 'var'")
        names.append(first_id.value)

        while self._match_delim(","):
            next_id = self._expect_id("esperado identificador após ','")
            names.append(next_id.value)

        self._match_delim(":")  # Opcional conforme EBNF

        var_type = self.parse_type()
        self._expect_delim(";", "esperado ';' após declaração de variável")

        return VarDeclNode(var_tok.line, var_tok.column, names, var_type)

    def parse_type(self) -> DataType:
        """Tipo ::= 'inteiro' | 'booleano' ;"""
        if self._match_keyword("inteiro"):
            return DataType.INTEIRO
        if self._match_keyword("booleano"):
            return DataType.BOOLEANO
        self._report_expected("esperado tipo ('inteiro' ou 'booleano')")
        raise _ParseSyncError()

    def parse_statement(self) -> AstNode:
        """Comando ::= Bloco | CmdAtrib | CmdSe | CmdEnquanto | CmdLeia | CmdEscreva | CmdPara | CmdRepita ;"""
        if self._check_delim("{"):
            return self.parse_block()
        if self._check(TokenType.ID):
            return self.parse_assign()
        if self._check_keyword("se"):
            return self.parse_if()
        if self._check_keyword("enquanto"):
            return self.parse_while()
        if self._check_keyword("leia"):
            return self.parse_read()
        if self._check_keyword("escreva"):
            return self.parse_write()
        if self._check_keyword("para"):
            return self.parse_for()
        if self._check_keyword("repita"):
            return self.parse_repeat()

        if self._check_keyword("senão"):
            self._report_raw("'senão' inesperado sem 'se' correspondente")
        else:
            self._report_expected("esperado comando válido")
        raise _ParseSyncError()

    def parse_assign(self) -> AssignNode:
        """CmdAtrib ::= ID '=' Expressao ';' ;"""
        id_tok = self._expect_id("esperado identificador")
        self._expect(TokenType.ASSIGN, "=", "esperado '=' na atribuição")
        expr = self.parse_expression()
        self._expect_delim(";", "esperado ';' após atribuição")
        return AssignNode(id_tok.line, id_tok.column, id_tok.value, expr)

    def _parse_parenthesized_condition(self, construct_name: str) -> ExprNode:
        """Analisa '( Expressao )' com recuperação local até ')' ou '{'."""
        try:
            self._expect_delim("(", f"esperado '(' após '{construct_name}'")
            expr = self.parse_expression()
            self._expect_delim(")", f"esperado ')' após condição de '{construct_name}'")
            return expr
        except _ParseSyncError:
            while not self._is_at_end():
                if self._check_delim(")"):
                    err_tok = self._advance()
                    return LiteralNode(err_tok.line, err_tok.column, False, DataType.ERROR)
                if self._check_delim("{"):
                    return LiteralNode(
                        self.current_token.line,
                        self.current_token.column,
                        False,
                        DataType.ERROR,
                    )
                if (
                    self._check_delim(";")
                    or self._check_delim("}")
                    or self._is_sync_keyword()
                ):
                    raise
                self._advance()
            raise

    def parse_if(self) -> IfNode:
        """CmdSe ::= 'se' '(' Expressao ')' Comando [ 'senão' Comando ] ;

        Resolução do Dangling Else por casamento guloso (greedy matching):
        após analisar o ramo 'then', verifica imediatamente se há 'senão',
        vinculando-o sempre ao 'se' mais próximo ainda aberto.
        """
        se_tok = self._expect_keyword("se", "esperado 'se'")
        condition = self._parse_parenthesized_condition("se")

        start_idx = self._token_index
        try:
            then_branch: AstNode = self.parse_statement()
        except _ParseSyncError:
            if (
                self._token_index == start_idx
                and not self._check_delim("}")
                and not self._check_keyword("fim")
                and not self._check_keyword("senão")
                and not self._is_at_end()
            ):
                self._advance()
            self.synchronize(extra_keywords={"senão"})
            then_branch = BlockNode(se_tok.line, se_tok.column, [], [])

        else_branch: AstNode | None = None
        if self._match_keyword("senão"):
            else_branch = self.parse_statement()

        return IfNode(se_tok.line, se_tok.column, condition, then_branch, else_branch)

    def parse_while(self) -> WhileNode:
        """CmdEnquanto ::= 'enquanto' '(' Expressao ')' Comando ;"""
        tok = self._expect_keyword("enquanto", "esperado 'enquanto'")
        condition = self._parse_parenthesized_condition("enquanto")
        body = self.parse_statement()
        return WhileNode(tok.line, tok.column, condition, body)

    def parse_read(self) -> ReadNode:
        """CmdLeia ::= 'leia' ( '(' ID ')' | ID ) ';' ;"""
        tok = self._expect_keyword("leia", "esperado 'leia'")
        if self._match_delim("("):
            id_tok = self._expect_id("esperado identificador em 'leia'")
            self._expect_delim(")", "esperado ')' após identificador em 'leia'")
        else:
            id_tok = self._expect_id("esperado identificador em 'leia'")
        self._expect_delim(";", "esperado ';' após comando 'leia'")
        return ReadNode(tok.line, tok.column, id_tok.value)

    def parse_write(self) -> WriteNode:
        """CmdEscreva ::= 'escreva' Expressao ';' ;"""
        tok = self._expect_keyword("escreva", "esperado 'escreva'")
        expr = self.parse_expression()
        self._expect_delim(";", "esperado ';' após comando 'escreva'")
        return WriteNode(tok.line, tok.column, expr)

    def parse_for(self) -> ForNode:
        """CmdPara ::= 'para' ID '=' Expressao 'ate' Expressao [ 'passo' Expressao ] Comando ;"""
        tok = self._expect_keyword("para", "esperado 'para'")
        id_tok = self._expect_id("esperado identificador de controle após 'para'")
        self._expect(
            TokenType.ASSIGN, "=", "esperado '=' após identificador em 'para'"
        )
        start = self.parse_expression()
        self._expect_keyword("ate", "esperado 'ate' no comando 'para'")
        end = self.parse_expression()
        step: ExprNode | None = None
        if self._match_keyword("passo"):
            step = self.parse_expression()
        body = self.parse_statement()
        return ForNode(tok.line, tok.column, id_tok.value, start, end, step, body)

    def parse_repeat(self) -> RepeatNode:
        """CmdRepita ::= 'repita' Comando 'ate' '(' Expressao ')' ';' ;"""
        tok = self._expect_keyword("repita", "esperado 'repita'")
        start_idx = self._token_index
        try:
            body: AstNode = self.parse_statement()
        except _ParseSyncError:
            if (
                self._token_index == start_idx
                and not self._check_delim("}")
                and not self._check_keyword("fim")
                and not self._check_keyword("ate")
                and not self._is_at_end()
            ):
                self._advance()
            self.synchronize(extra_keywords={"ate"})
            body = BlockNode(tok.line, tok.column, [], [])

        self._expect_keyword("ate", "esperado 'ate' após corpo de 'repita'")
        condition = self._parse_parenthesized_condition("ate")
        self._expect_delim(";", "esperado ';' após comando 'repita'")
        return RepeatNode(tok.line, tok.column, body, condition)

    def parse_expression(self) -> ExprNode:
        """Expressao ::= ExprOu ;"""
        return self.parse_expr_ou()

    def parse_expr_ou(self) -> ExprNode:
        """ExprOu ::= ExprE { 'ou' ExprE } ; (associativo à esquerda)"""
        left = self.parse_expr_e()
        while (op_tok := self._match_op_logico("ou")) is not None:
            right = self.parse_expr_e()
            left = BinOpNode(op_tok.line, op_tok.column, left, op_tok.value, right)
        return left

    def parse_expr_e(self) -> ExprNode:
        """ExprE ::= ExprRel { 'e' ExprRel } ; (associativo à esquerda)"""
        left = self.parse_expr_rel()
        while (op_tok := self._match_op_logico("e")) is not None:
            right = self.parse_expr_rel()
            left = BinOpNode(op_tok.line, op_tok.column, left, op_tok.value, right)
        return left

    def parse_expr_rel(self) -> ExprNode:
        """ExprRel ::= ExprAdit [ ( '==' | '!=' | '<' | '<=' | '>' | '>=' ) ExprAdit ] ;"""
        left = self.parse_expr_adit()
        if self._check(TokenType.OP_REL):
            op_tok = self._advance()
            right = self.parse_expr_adit()
            return BinOpNode(op_tok.line, op_tok.column, left, op_tok.value, right)
        return left

    def parse_expr_adit(self) -> ExprNode:
        """ExprAdit ::= ExprMult { ( '+' | '-' ) ExprMult } ; (associativo à esquerda)"""
        left = self.parse_expr_mult()
        while (
            self._check(TokenType.OP_ARIT)
            and self.current_token.value in {"+", "-"}
        ):
            op_tok = self._advance()
            right = self.parse_expr_mult()
            left = BinOpNode(op_tok.line, op_tok.column, left, op_tok.value, right)
        return left

    def parse_expr_mult(self) -> ExprNode:
        """ExprMult ::= ExprUnaria { ( '*' | '/' | '%' ) ExprUnaria } ; (associativo à esquerda)"""
        left = self.parse_expr_unaria()
        while (
            self._check(TokenType.OP_ARIT)
            and self.current_token.value in {"*", "/", "%"}
        ):
            op_tok = self._advance()
            right = self.parse_expr_unaria()
            left = BinOpNode(op_tok.line, op_tok.column, left, op_tok.value, right)
        return left

    def parse_expr_unaria(self) -> ExprNode:
        """ExprUnaria ::= ( 'não' | '-' ) ExprUnaria | Primario ;"""
        if (
            self._check(TokenType.OP_LOGICO) and self.current_token.value == "não"
        ) or (self._check(TokenType.OP_ARIT) and self.current_token.value == "-"):
            op_tok = self._advance()
            operand = self.parse_expr_unaria()
            return UnaryOpNode(op_tok.line, op_tok.column, op_tok.value, operand)
        return self.parse_primary()

    def parse_primary(self) -> ExprNode:
        """Primario ::= INT | 'verdadeiro' | 'falso' | ID | '(' Expressao ')' ;"""
        tok = self.current_token

        if tok.type == TokenType.INT:
            self._advance()
            return LiteralNode(tok.line, tok.column, int(tok.value), DataType.INTEIRO)

        if self._match_keyword("verdadeiro"):
            return LiteralNode(tok.line, tok.column, True, DataType.BOOLEANO)

        if self._match_keyword("falso"):
            return LiteralNode(tok.line, tok.column, False, DataType.BOOLEANO)

        if tok.type == TokenType.ID:
            self._advance()
            return VarNode(tok.line, tok.column, tok.value)

        if self._match_delim("("):
            expr = self.parse_expression()
            self._expect_delim(")", "esperado ')' após expressão")
            return expr

        self._report_expected("esperado expressão")
        raise _ParseSyncError()
