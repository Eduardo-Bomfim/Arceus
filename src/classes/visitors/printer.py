from __future__ import annotations
from src.classes.ast_nodes import (
    AssignNode,
    AstNode,
    AstVisitor,
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
from src.enum.data_type import DataType

def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())

def _type_annotation(node: ExprNode) -> str:
    if node.inferred_type is None:
        return ""
    return f" [{node.inferred_type.name}]"

class PrintAstVisitor(AstVisitor):
    """Pretty Printer da AST para inspeção visual e depuração."""

    def format(self, node: AstNode) -> str:
        return node.accept(self)

    def visit_program(self, node: ProgramNode) -> str:
        lines = [f"Program(name='{node.name}')"]
        lines.append(_indent(node.block.accept(self)))
        return "\n".join(lines)

    def visit_block(self, node: BlockNode) -> str:
        lines = ["Block"]
        for decl in node.declarations:
            lines.append(_indent(decl.accept(self)))
        for stmt in node.statements:
            lines.append(_indent(stmt.accept(self)))
        return "\n".join(lines)

    def visit_var_decl(self, node: VarDeclNode) -> str:
        names_str = ", ".join(repr(name) for name in node.names)
        return f"VarDecl(names=[{names_str}], type={node.var_type.name})"

    def visit_assign(self, node: AssignNode) -> str:
        lines = [f"Assign(name='{node.name}')"]
        lines.append(_indent(node.expr.accept(self)))
        return "\n".join(lines)

    def visit_if(self, node: IfNode) -> str:
        lines = ["If"]
        lines.append(_indent("condition:"))
        lines.append(_indent(node.condition.accept(self), "    "))
        lines.append(_indent("then:"))
        lines.append(_indent(node.then_branch.accept(self), "    "))
        if node.else_branch is not None:
            lines.append(_indent("else:"))
            lines.append(_indent(node.else_branch.accept(self), "    "))
        return "\n".join(lines)

    def visit_while(self, node: WhileNode) -> str:
        lines = ["While"]
        lines.append(_indent("condition:"))
        lines.append(_indent(node.condition.accept(self), "    "))
        lines.append(_indent("body:"))
        lines.append(_indent(node.body.accept(self), "    "))
        return "\n".join(lines)

    def visit_read(self, node: ReadNode) -> str:
        return f"Read(name='{node.name}')"

    def visit_write(self, node: WriteNode) -> str:
        lines = ["Write"]
        lines.append(_indent(node.expr.accept(self)))
        return "\n".join(lines)

    def visit_for(self, node: ForNode) -> str:
        lines = [f"For(var='{node.var_name}')"]
        lines.append(_indent("start:"))
        lines.append(_indent(node.start.accept(self), "    "))
        lines.append(_indent("end:"))
        lines.append(_indent(node.end.accept(self), "    "))
        if node.step is not None:
            lines.append(_indent("step:"))
            lines.append(_indent(node.step.accept(self), "    "))
        lines.append(_indent("body:"))
        lines.append(_indent(node.body.accept(self), "    "))
        return "\n".join(lines)

    def visit_repeat(self, node: RepeatNode) -> str:
        lines = ["Repeat"]
        lines.append(_indent("body:"))
        lines.append(_indent(node.body.accept(self), "    "))
        lines.append(_indent("until:"))
        lines.append(_indent(node.condition.accept(self), "    "))
        return "\n".join(lines)

    def visit_bin_op(self, node: BinOpNode) -> str:
        lines = [f"BinOp(op='{node.op}'){_type_annotation(node)}"]
        lines.append(_indent(node.left.accept(self)))
        lines.append(_indent(node.right.accept(self)))
        return "\n".join(lines)

    def visit_unary_op(self, node: UnaryOpNode) -> str:
        lines = [f"UnaryOp(op='{node.op}'){_type_annotation(node)}"]
        lines.append(_indent(node.operand.accept(self)))
        return "\n".join(lines)

    def visit_literal(self, node: LiteralNode) -> str:
        if node.literal_type == DataType.BOOLEANO:
            value_str = "verdadeiro" if node.value else "falso"
        else:
            value_str = str(node.value)
        return f"Literal({value_str}, {node.literal_type.name}){_type_annotation(node)}"

    def visit_var(self, node: VarNode) -> str:
        return f"Var(name='{node.name}'){_type_annotation(node)}"
