from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from src.enum.data_type import DataType

class AstVisitor(ABC):
    """Interface Visitor para percurso desacoplado sobre a AST da MiniLang."""

    @abstractmethod
    def visit_program(self, node: ProgramNode): ...

    @abstractmethod
    def visit_block(self, node: BlockNode): ...

    @abstractmethod
    def visit_var_decl(self, node: VarDeclNode): ...

    @abstractmethod
    def visit_assign(self, node: AssignNode): ...

    @abstractmethod
    def visit_if(self, node: IfNode): ...

    @abstractmethod
    def visit_while(self, node: WhileNode): ...

    @abstractmethod
    def visit_read(self, node: ReadNode): ...

    @abstractmethod
    def visit_write(self, node: WriteNode): ...

    @abstractmethod
    def visit_for(self, node: ForNode): ...

    @abstractmethod
    def visit_repeat(self, node: RepeatNode): ...

    @abstractmethod
    def visit_bin_op(self, node: BinOpNode): ...

    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode): ...

    @abstractmethod
    def visit_literal(self, node: LiteralNode): ...

    @abstractmethod
    def visit_var(self, node: VarNode): ...

@dataclass
class AstNode(ABC):
    """Nó base da Árvore Sintática Abstrata com coordenadas de origem."""

    line: int
    column: int

    @abstractmethod
    def accept(self, visitor: AstVisitor): ...

@dataclass
class ExprNode(AstNode, ABC):
    """Nó base para expressões, preparado para anotação de tipo na fase semântica."""

    inferred_type: DataType | None = field(default=None, init=False)

@dataclass
class ProgramNode(AstNode):
    name: str
    block: BlockNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_program(self)

@dataclass
class BlockNode(AstNode):
    declarations: list[VarDeclNode]
    statements: list[AstNode]

    def accept(self, visitor: AstVisitor):
        return visitor.visit_block(self)

@dataclass
class VarDeclNode(AstNode):
    names: list[str]
    var_type: DataType

    def accept(self, visitor: AstVisitor):
        return visitor.visit_var_decl(self)

@dataclass
class AssignNode(AstNode):
    name: str
    expr: ExprNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_assign(self)

@dataclass
class IfNode(AstNode):
    condition: ExprNode
    then_branch: AstNode
    else_branch: AstNode | None = None

    def accept(self, visitor: AstVisitor):
        return visitor.visit_if(self)

@dataclass
class WhileNode(AstNode):
    condition: ExprNode
    body: AstNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_while(self)

@dataclass
class ReadNode(AstNode):
    name: str

    def accept(self, visitor: AstVisitor):
        return visitor.visit_read(self)

@dataclass
class WriteNode(AstNode):
    expr: ExprNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_write(self)

@dataclass
class ForNode(AstNode):
    """Laço contado 'para' (Extensão Obrigatória — Opção D)."""

    var_name: str
    start: ExprNode
    end: ExprNode
    step: ExprNode | None
    body: AstNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_for(self)

@dataclass
class RepeatNode(AstNode):
    """Laço pós-testado 'repita ... ate (...)' (Extensão Obrigatória — Opção D)."""

    body: AstNode
    condition: ExprNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_repeat(self)

@dataclass
class BinOpNode(ExprNode):
    left: ExprNode
    op: str
    right: ExprNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_bin_op(self)

@dataclass
class UnaryOpNode(ExprNode):
    op: str
    operand: ExprNode

    def accept(self, visitor: AstVisitor):
        return visitor.visit_unary_op(self)

@dataclass
class LiteralNode(ExprNode):
    value: int | bool
    literal_type: DataType

    def accept(self, visitor: AstVisitor):
        return visitor.visit_literal(self)

@dataclass
class VarNode(ExprNode):
    name: str

    def accept(self, visitor: AstVisitor):
        return visitor.visit_var(self)
