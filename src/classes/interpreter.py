from __future__ import annotations
import sys
from typing import Callable
from src.classes.ast_nodes import (
    AssignNode,
    AstNode,
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
from src.enum.data_type import DataType

class ExecutionError(Exception):
    """Exceção levantada em tempo de execução pelo Interpretador MiniLang."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return self.message

class Interpreter(AstVisitor):
    """Interpretador direto da AST da MiniLang com suporte a escopos, runtime I/O e limite de passos."""

    def __init__(
        self,
        input_fn: Callable[[str], str] | None = None,
        output_fn: Callable[[str], None] | None = None,
        max_steps: int | None = None,
        emit_errors: bool = True,
    ) -> None:
        self.input_fn: Callable[[str], str] = input_fn if input_fn is not None else input
        self.output_fn: Callable[[str], None] = output_fn if output_fn is not None else print
        self.max_steps: int | None = max_steps
        self.emit_errors: bool = emit_errors

        self.environments: list[dict[str, int | bool]] = []
        self.type_environments: list[dict[str, DataType]] = []
        self.output_history: list[str] = []
        self.errors: list[str] = []
        self.step_count: int = 0

    def interpret(self, program: ProgramNode) -> bool:
        """Executa o programa a partir do nó raiz ProgramNode.

        Retorna True se executado com sucesso ou False se houver erro de execução.
        """
        self.environments = []
        self.type_environments = []
        self.output_history = []
        self.errors = []
        self.step_count = 0

        try:
            program.accept(self)
            return True
        except ExecutionError as err:
            err_msg = str(err)
            self.errors.append(err_msg)
            if self.emit_errors:
                print(err_msg, file=sys.stderr)
            return False

    def _check_step(self, node: AstNode) -> None:
        self.step_count += 1
        if self.max_steps is not None and self.step_count > self.max_steps:
            raise ExecutionError(
                f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: limite máximo de passos ({self.max_steps}) excedido",
                node.line,
                node.column,
            )

    def enter_scope(self) -> None:
        self.environments.append({})
        self.type_environments.append({})

    def exit_scope(self) -> None:
        if self.environments:
            self.environments.pop()
            self.type_environments.pop()

    def get_variable_type(self, name: str) -> DataType:
        for env in reversed(self.type_environments):
            if name in env:
                return env[name]
        return DataType.INTEIRO

    def set_variable(self, name: str, value: int | bool) -> None:
        for env in reversed(self.environments):
            if name in env:
                env[name] = value
                return
        if self.environments:
            self.environments[-1][name] = value

    def get_variable(self, name: str, line: int, column: int) -> int | bool:
        for env in reversed(self.environments):
            if name in env:
                return env[name]
        raise ExecutionError(
            f"[Erro de Execução] Linha {line}, Coluna {column}: variável '{name}' não inicializada no ambiente de execução",
            line,
            column,
        )

    def visit_program(self, node: ProgramNode) -> None:
        node.block.accept(self)

    def visit_block(self, node: BlockNode) -> None:
        self.enter_scope()
        try:
            for decl in node.declarations:
                decl.accept(self)
            for stmt in node.statements:
                self._check_step(stmt)
                stmt.accept(self)
        finally:
            self.exit_scope()

    def visit_var_decl(self, node: VarDeclNode) -> None:
        for name in node.names:
            self.type_environments[-1][name] = node.var_type
            default_val = 0 if node.var_type == DataType.INTEIRO else False
            self.environments[-1][name] = default_val

    def visit_assign(self, node: AssignNode) -> None:
        val = node.expr.accept(self)
        self.set_variable(node.name, val)

    def visit_if(self, node: IfNode) -> None:
        cond = node.condition.accept(self)
        if cond:
            node.then_branch.accept(self)
        elif node.else_branch is not None:
            node.else_branch.accept(self)

    def visit_while(self, node: WhileNode) -> None:
        while True:
            self._check_step(node)
            cond = node.condition.accept(self)
            if not cond:
                break
            node.body.accept(self)

    def visit_read(self, node: ReadNode) -> None:
        var_type = self.get_variable_type(node.name)
        try:
            raw = self.input_fn("")
        except EOFError:
            raise ExecutionError(
                f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: fim inesperado da entrada (EOF) ao ler '{node.name}'",
                node.line,
                node.column,
            )

        raw_clean = raw.strip()

        if var_type == DataType.INTEIRO:
            try:
                val = int(raw_clean)
            except ValueError:
                raise ExecutionError(
                    f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: entrada inválida para variável inteira '{node.name}': '{raw}'",
                    node.line,
                    node.column,
                )
        elif var_type == DataType.BOOLEANO:
            lowered = raw_clean.lower()
            if lowered in {"verdadeiro", "true", "1"}:
                val = True
            elif lowered in {"falso", "false", "0"}:
                val = False
            else:
                raise ExecutionError(
                    f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: entrada inválida para variável booleana '{node.name}': esperado 'verdadeiro' ou 'falso', encontrado '{raw}'",
                    node.line,
                    node.column,
                )
        else:
            val = int(raw_clean)

        self.set_variable(node.name, val)

    def visit_write(self, node: WriteNode) -> None:
        val = node.expr.accept(self)
        if isinstance(val, bool):
            text = "verdadeiro" if val else "falso"
        else:
            text = str(val)
        self.output_fn(text)
        self.output_history.append(text)

    def visit_for(self, node: ForNode) -> None:
        start_val = node.start.accept(self)
        end_val = node.end.accept(self)
        step_val = node.step.accept(self) if node.step is not None else 1

        if step_val == 0:
            raise ExecutionError(
                f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: passo do laço 'para' não pode ser zero",
                node.line,
                node.column,
            )

        self.set_variable(node.var_name, start_val)

        while True:
            self._check_step(node)
            curr = self.get_variable(node.var_name, node.line, node.column)
            if step_val > 0 and curr > end_val:
                break
            if step_val < 0 and curr < end_val:
                break
            node.body.accept(self)
            curr = self.get_variable(node.var_name, node.line, node.column)
            self.set_variable(node.var_name, curr + step_val)

    def visit_repeat(self, node: RepeatNode) -> None:
        while True:
            self._check_step(node)
            node.body.accept(self)
            cond = node.condition.accept(self)
            if cond:
                break

    def visit_bin_op(self, node: BinOpNode) -> int | bool:
        # Avaliação com curto-circuito para operadores lógicos
        if node.op == "e":
            left_val = node.left.accept(self)
            if not left_val:
                return False
            return bool(node.right.accept(self))

        if node.op == "ou":
            left_val = node.left.accept(self)
            if left_val:
                return True
            return bool(node.right.accept(self))

        left = node.left.accept(self)
        right = node.right.accept(self)

        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise ExecutionError(
                    f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: divisão por zero",
                    node.line,
                    node.column,
                )
            return left // right
        if node.op == "%":
            if right == 0:
                raise ExecutionError(
                    f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: divisão por zero no operador '%'",
                    node.line,
                    node.column,
                )
            return left % right

        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        if node.op == "<":
            return left < right
        if node.op == "<=":
            return left <= right
        if node.op == ">":
            return left > right
        if node.op == ">=":
            return left >= right

        raise ExecutionError(
            f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: operador binário desconhecido '{node.op}'",
            node.line,
            node.column,
        )

    def visit_unary_op(self, node: UnaryOpNode) -> int | bool:
        operand = node.operand.accept(self)
        if node.op == "-":
            return -operand
        if node.op == "não":
            return not operand
        raise ExecutionError(
            f"[Erro de Execução] Linha {node.line}, Coluna {node.column}: operador unário desconhecido '{node.op}'",
            node.line,
            node.column,
        )

    def visit_literal(self, node: LiteralNode) -> int | bool:
        return node.value

    def visit_var(self, node: VarNode) -> int | bool:
        return self.get_variable(node.name, node.line, node.column)
