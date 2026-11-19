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

class ConstantFolder(AstVisitor):
    """Pass de otimização AST -> AST que realiza Constant Folding (dobramento de constantes) e simplificação de expressões e desvios condicionais com operandos literais.
    """

    def optimize(self, node: AstNode) -> AstNode:
        """Ponto de entrada do otimizador: percorre a AST e retorna uma nova árvore otimizada."""
        return node.accept(self)

    def visit_program(self, node: ProgramNode) -> ProgramNode:
        opt_block = node.block.accept(self)
        return ProgramNode(node.line, node.column, node.name, opt_block)

    def visit_block(self, node: BlockNode) -> BlockNode:
        opt_declarations = [decl.accept(self) for decl in node.declarations]
        opt_statements = [stmt.accept(self) for stmt in node.statements]
        return BlockNode(node.line, node.column, opt_declarations, opt_statements)

    def visit_var_decl(self, node: VarDeclNode) -> VarDeclNode:
        return VarDeclNode(node.line, node.column, list(node.names), node.var_type)

    def visit_assign(self, node: AssignNode) -> AssignNode:
        opt_expr = node.expr.accept(self)
        return AssignNode(node.line, node.column, node.name, opt_expr)

    def visit_if(self, node: IfNode) -> IfNode:
        opt_cond = node.condition.accept(self)
        opt_then = node.then_branch.accept(self)
        opt_else = (
            node.else_branch.accept(self) if node.else_branch is not None else None
        )

        # Simplificação de desvio com condição constante
        if isinstance(opt_cond, LiteralNode) and opt_cond.literal_type == DataType.BOOLEANO:
            if opt_cond.value is True:
                # O ramo 'then' sempre executará; o 'senão' torna-se código morto
                return IfNode(node.line, node.column, opt_cond, opt_then, None)
            else:
                # A condição é sempre falsa; o ramo 'then' torna-se código morto
                empty_block = BlockNode(node.line, node.column, [], [])
                return IfNode(node.line, node.column, opt_cond, empty_block, opt_else)

        return IfNode(node.line, node.column, opt_cond, opt_then, opt_else)

    def visit_while(self, node: WhileNode) -> WhileNode:
        opt_cond = node.condition.accept(self)
        opt_body = node.body.accept(self)
        return WhileNode(node.line, node.column, opt_cond, opt_body)

    def visit_read(self, node: ReadNode) -> ReadNode:
        return ReadNode(node.line, node.column, node.name)

    def visit_write(self, node: WriteNode) -> WriteNode:
        opt_expr = node.expr.accept(self)
        return WriteNode(node.line, node.column, opt_expr)

    def visit_for(self, node: ForNode) -> ForNode:
        opt_start = node.start.accept(self)
        opt_end = node.end.accept(self)
        opt_step = node.step.accept(self) if node.step is not None else None
        opt_body = node.body.accept(self)
        return ForNode(
            node.line,
            node.column,
            node.var_name,
            opt_start,
            opt_end,
            opt_step,
            opt_body,
        )

    def visit_repeat(self, node: RepeatNode) -> RepeatNode:
        opt_body = node.body.accept(self)
        opt_cond = node.condition.accept(self)
        return RepeatNode(node.line, node.column, opt_body, opt_cond)

    def visit_bin_op(self, node: BinOpNode) -> ExprNode:
        left: ExprNode = node.left.accept(self)
        right: ExprNode = node.right.accept(self)

        # 1. Dobramento completo quando ambos os operandos são literais
        if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
            val_left = left.value
            val_right = right.value

            # Aritméticos
            if node.op == "+":
                res = LiteralNode(node.line, node.column, val_left + val_right, DataType.INTEIRO)
                res.inferred_type = DataType.INTEIRO
                return res
            if node.op == "-":
                res = LiteralNode(node.line, node.column, val_left - val_right, DataType.INTEIRO)
                res.inferred_type = DataType.INTEIRO
                return res
            if node.op == "*":
                res = LiteralNode(node.line, node.column, val_left * val_right, DataType.INTEIRO)
                res.inferred_type = DataType.INTEIRO
                return res
            if node.op == "/":
                if val_right != 0:
                    res = LiteralNode(node.line, node.column, val_left // val_right, DataType.INTEIRO)
                    res.inferred_type = DataType.INTEIRO
                    return res
                # Se for divisão por zero em tempo de compilação, não dobra (delega ao runtime)
            if node.op == "%":
                if val_right != 0:
                    res = LiteralNode(node.line, node.column, val_left % val_right, DataType.INTEIRO)
                    res.inferred_type = DataType.INTEIRO
                    return res

            # Relacionais
            if node.op == "==":
                res = LiteralNode(node.line, node.column, val_left == val_right, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if node.op == "!=":
                res = LiteralNode(node.line, node.column, val_left != val_right, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if node.op == "<":
                res = LiteralNode(node.line, node.column, val_left < val_right, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if node.op == "<=":
                res = LiteralNode(node.line, node.column, val_left <= val_right, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if node.op == ">":
                res = LiteralNode(node.line, node.column, val_left > val_right, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if node.op == ">=":
                res = LiteralNode(node.line, node.column, val_left >= val_right, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res

            # Lógicos
            if node.op == "e":
                res = LiteralNode(node.line, node.column, bool(val_left and val_right), DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if node.op == "ou":
                res = LiteralNode(node.line, node.column, bool(val_left or val_right), DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res

        # 2. Simplificações lógicas com elemento absorvente (curto-circuito estático)
        if node.op == "e":
            if isinstance(left, LiteralNode) and left.value is False:
                res = LiteralNode(node.line, node.column, False, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if isinstance(left, LiteralNode) and left.value is True:
                return right
        elif node.op == "ou":
            if isinstance(left, LiteralNode) and left.value is True:
                res = LiteralNode(node.line, node.column, True, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res
            if isinstance(left, LiteralNode) and left.value is False:
                return right

        new_bin = BinOpNode(node.line, node.column, left, node.op, right)
        new_bin.inferred_type = node.inferred_type
        return new_bin

    def visit_unary_op(self, node: UnaryOpNode) -> ExprNode:
        operand: ExprNode = node.operand.accept(self)

        if isinstance(operand, LiteralNode):
            if node.op == "-":
                res = LiteralNode(node.line, node.column, -operand.value, DataType.INTEIRO)
                res.inferred_type = DataType.INTEIRO
                return res
            if node.op == "não":
                res = LiteralNode(node.line, node.column, not operand.value, DataType.BOOLEANO)
                res.inferred_type = DataType.BOOLEANO
                return res

        new_unary = UnaryOpNode(node.line, node.column, node.op, operand)
        new_unary.inferred_type = node.inferred_type
        return new_unary

    def visit_literal(self, node: LiteralNode) -> LiteralNode:
        res = LiteralNode(node.line, node.column, node.value, node.literal_type)
        res.inferred_type = node.inferred_type or node.literal_type
        return res

    def visit_var(self, node: VarNode) -> VarNode:
        res = VarNode(node.line, node.column, node.name)
        res.inferred_type = node.inferred_type
        return res
