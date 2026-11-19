from __future__ import annotations
import sys
from src.classes.ast_nodes import (
    AssignNode,
    AstVisitor,
    BinOpNode,
    BlockNode,
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
from src.classes.symbol_table import Symbol, SymbolTable
from src.enum.data_type import DataType

class SemanticAnalyzer(AstVisitor):
    """Analisador Semântico baseado em AstVisitor com escopos, tipos e inicialização."""

    ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}
    ORDERING_OPS = {"<", "<=", ">", ">="}
    EQUALITY_OPS = {"==", "!="}
    LOGICAL_OPS = {"e", "ou"}

    def __init__(self, emit_errors: bool = True) -> None:
        self.emit_errors = emit_errors
        self.symbol_table = SymbolTable()
        self.errors: list[str] = []

    def analyze(self, program: ProgramNode) -> bool:
        """Executa a análise semântica sobre a AST e retorna True se não houver erros."""
        self.symbol_table = SymbolTable()
        self.errors = []
        program.accept(self)
        return len(self.errors) == 0

    def _report_error(self, line: int, column: int, description: str) -> None:
        formatted = f"[Erro Semântico] Linha {line}, Coluna {column}: {description}"
        self.errors.append(formatted)
        if self.emit_errors:
            print(formatted, file=sys.stderr)

    def _check_boolean_condition(self, expr, construct_name: str) -> None:
        cond_type = expr.accept(self)
        if cond_type != DataType.ERROR and cond_type != DataType.BOOLEANO:
            self._report_error(
                expr.line,
                expr.column,
                f"condição do comando '{construct_name}' deve ser do tipo BOOLEANO, "
                f"encontrado {cond_type.name}",
            )

    def visit_program(self, node: ProgramNode) -> None:
        node.block.accept(self)

    def visit_block(self, node: BlockNode) -> None:
        self.symbol_table.enter_scope()
        try:
            for decl in node.declarations:
                decl.accept(self)
            for stmt in node.statements:
                stmt.accept(self)
        finally:
            self.symbol_table.exit_scope()

    def visit_var_decl(self, node: VarDeclNode) -> None:
        for name in node.names:
            existing = self.symbol_table.lookup_local(name)
            if existing is not None:
                self._report_error(
                    node.line,
                    node.column,
                    f"variável '{name}' já declarada neste escopo "
                    f"(declaração anterior na Linha {existing.line}, Coluna {existing.column})",
                )
            else:
                self.symbol_table.declare(
                    Symbol(
                        name=name,
                        data_type=node.var_type,
                        line=node.line,
                        column=node.column,
                        initialized=False,
                    )
                )

    def visit_assign(self, node: AssignNode) -> None:
        # Avalia a expressão antes de marcar o alvo como inicializado (ex.: x = x + 1;)
        expr_type = node.expr.accept(self)
        symbol = self.symbol_table.lookup(node.name)

        if symbol is None:
            self._report_error(
                node.line,
                node.column,
                f"variável '{node.name}' não declarada",
            )
            return

        if expr_type != DataType.ERROR and symbol.data_type != expr_type:
            self._report_error(
                node.line,
                node.column,
                f"incompatibilidade de tipos na atribuição à variável '{node.name}': "
                f"esperado {symbol.data_type.name}, encontrado {expr_type.name}",
            )

        symbol.initialized = True

    def visit_if(self, node: IfNode) -> None:
        self._check_boolean_condition(node.condition, "se")

        before = self.symbol_table.snapshot_initialization()
        node.then_branch.accept(self)
        after_then = self.symbol_table.snapshot_initialization()

        if node.else_branch is not None:
            self.symbol_table.restore_initialization(before)
            node.else_branch.accept(self)
            after_else = self.symbol_table.snapshot_initialization()
            self.symbol_table.intersect_initialization(before, after_then, after_else)
        else:
            # Sem 'senão', o ramo 'then' pode não executar
            self.symbol_table.restore_initialization(before)

    def visit_while(self, node: WhileNode) -> None:
        self._check_boolean_condition(node.condition, "enquanto")

        before = self.symbol_table.snapshot_initialization()
        node.body.accept(self)
        # Um laço 'enquanto' pode executar zero vezes
        self.symbol_table.restore_initialization(before)

    def visit_read(self, node: ReadNode) -> None:
        symbol = self.symbol_table.lookup(node.name)
        if symbol is None:
            self._report_error(
                node.line,
                node.column,
                f"variável '{node.name}' não declarada em 'leia'",
            )
            return
        symbol.initialized = True

    def visit_write(self, node: WriteNode) -> None:
        node.expr.accept(self)

    def visit_for(self, node: ForNode) -> None:
        start_type = node.start.accept(self)
        if start_type != DataType.ERROR and start_type != DataType.INTEIRO:
            self._report_error(
                node.start.line,
                node.start.column,
                f"expressão inicial do comando 'para' deve ser do tipo INTEIRO, "
                f"encontrado {start_type.name}",
            )

        end_type = node.end.accept(self)
        if end_type != DataType.ERROR and end_type != DataType.INTEIRO:
            self._report_error(
                node.end.line,
                node.end.column,
                f"expressão final do comando 'para' deve ser do tipo INTEIRO, "
                f"encontrado {end_type.name}",
            )

        if node.step is not None:
            step_type = node.step.accept(self)
            if step_type != DataType.ERROR and step_type != DataType.INTEIRO:
                self._report_error(
                    node.step.line,
                    node.step.column,
                    f"expressão de passo do comando 'para' deve ser do tipo INTEIRO, "
                    f"encontrado {step_type.name}",
                )

        symbol = self.symbol_table.lookup(node.var_name)
        if symbol is None:
            self._report_error(
                node.line,
                node.column,
                f"variável de controle '{node.var_name}' do comando 'para' não declarada",
            )
        else:
            if symbol.data_type != DataType.INTEIRO:
                self._report_error(
                    node.line,
                    node.column,
                    f"variável de controle '{node.var_name}' do comando 'para' deve ser "
                    f"do tipo INTEIRO, encontrado {symbol.data_type.name}",
                )
            # A variável de controle recebe o valor inicial antes do primeiro teste
            symbol.initialized = True

        before_body = self.symbol_table.snapshot_initialization()
        node.body.accept(self)
        # O corpo do 'para' pode executar zero vezes (mas a variável de controle segue inicializada)
        self.symbol_table.restore_initialization(before_body)

    def visit_repeat(self, node: RepeatNode) -> None:
        # 'repita' executa o corpo ao menos uma vez antes de testar 'ate (...)'
        node.body.accept(self)
        self._check_boolean_condition(node.condition, "repita/ate")

    def visit_bin_op(self, node: BinOpNode) -> DataType:
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)

        if left_type == DataType.ERROR or right_type == DataType.ERROR:
            node.inferred_type = DataType.ERROR
            return DataType.ERROR

        if node.op in self.ARITHMETIC_OPS:
            if left_type != DataType.INTEIRO or right_type != DataType.INTEIRO:
                self._report_error(
                    node.line,
                    node.column,
                    f"operador aritmético '{node.op}' exige operandos do tipo INTEIRO, "
                    f"encontrado {left_type.name} e {right_type.name}",
                )
                node.inferred_type = DataType.ERROR
                return DataType.ERROR
            node.inferred_type = DataType.INTEIRO
            return DataType.INTEIRO

        if node.op in self.ORDERING_OPS:
            if left_type != DataType.INTEIRO or right_type != DataType.INTEIRO:
                self._report_error(
                    node.line,
                    node.column,
                    f"operador relacional '{node.op}' exige operandos do tipo INTEIRO, "
                    f"encontrado {left_type.name} e {right_type.name}",
                )
                node.inferred_type = DataType.ERROR
                return DataType.ERROR
            node.inferred_type = DataType.BOOLEANO
            return DataType.BOOLEANO

        if node.op in self.EQUALITY_OPS:
            if left_type != right_type:
                self._report_error(
                    node.line,
                    node.column,
                    f"operador relacional '{node.op}' exige operandos do mesmo tipo, "
                    f"encontrado {left_type.name} e {right_type.name}",
                )
                node.inferred_type = DataType.ERROR
                return DataType.ERROR
            node.inferred_type = DataType.BOOLEANO
            return DataType.BOOLEANO

        if node.op in self.LOGICAL_OPS:
            if left_type != DataType.BOOLEANO or right_type != DataType.BOOLEANO:
                self._report_error(
                    node.line,
                    node.column,
                    f"operador lógico '{node.op}' exige operandos do tipo BOOLEANO, "
                    f"encontrado {left_type.name} e {right_type.name}",
                )
                node.inferred_type = DataType.ERROR
                return DataType.ERROR
            node.inferred_type = DataType.BOOLEANO
            return DataType.BOOLEANO

        self._report_error(
            node.line,
            node.column,
            f"operador binário desconhecido '{node.op}'",
        )
        node.inferred_type = DataType.ERROR
        return DataType.ERROR

    def visit_unary_op(self, node: UnaryOpNode) -> DataType:
        operand_type = node.operand.accept(self)

        if operand_type == DataType.ERROR:
            node.inferred_type = DataType.ERROR
            return DataType.ERROR

        if node.op == "-":
            if operand_type != DataType.INTEIRO:
                self._report_error(
                    node.line,
                    node.column,
                    f"operador unário '-' exige operando do tipo INTEIRO, "
                    f"encontrado {operand_type.name}",
                )
                node.inferred_type = DataType.ERROR
                return DataType.ERROR
            node.inferred_type = DataType.INTEIRO
            return DataType.INTEIRO

        if node.op == "não":
            if operand_type != DataType.BOOLEANO:
                self._report_error(
                    node.line,
                    node.column,
                    f"operador lógico 'não' exige operando do tipo BOOLEANO, "
                    f"encontrado {operand_type.name}",
                )
                node.inferred_type = DataType.ERROR
                return DataType.ERROR
            node.inferred_type = DataType.BOOLEANO
            return DataType.BOOLEANO

        self._report_error(
            node.line,
            node.column,
            f"operador unário desconhecido '{node.op}'",
        )
        node.inferred_type = DataType.ERROR
        return DataType.ERROR

    def visit_literal(self, node: LiteralNode) -> DataType:
        node.inferred_type = node.literal_type
        return node.literal_type

    def visit_var(self, node: VarNode) -> DataType:
        symbol = self.symbol_table.lookup(node.name)
        if symbol is None:
            self._report_error(
                node.line,
                node.column,
                f"variável '{node.name}' não declarada",
            )
            node.inferred_type = DataType.ERROR
            return DataType.ERROR

        if not symbol.initialized:
            self._report_error(
                node.line,
                node.column,
                f"variável '{node.name}' usada antes de ser inicializada",
            )

        node.inferred_type = symbol.data_type
        return symbol.data_type
