from pathlib import Path
import pytest

from main import main
from src.classes.ast_nodes import (
    AssignNode,
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
    WhileNode,
    WriteNode,
)
from src.classes.parser import Parser
from src.classes.scanner import Scanner
from src.classes.visitors.printer import PrintAstVisitor
from src.enum.data_type import DataType

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURES = sorted((FIXTURES_DIR / "valid").glob("*.ml"))
INVALID_SYNTAX_FIXTURES = sorted((FIXTURES_DIR / "invalid").glob("sintatico_*.ml"))

def parse_code(source: str, emit_errors: bool = False) -> tuple[ProgramNode | None, Parser]:
    scanner = Scanner(source)
    parser = Parser(scanner, emit_errors=emit_errors)
    ast = parser.parse()
    return ast, parser

def wrap_expr(expr: str, decls: str = "var x, y, z, a, b, c : inteiro; var ativo booleano;") -> str:
    return f"""
    programa teste {{
        {decls}
        ativo = {expr};
    }}
    fim.
    """

# =====================================================================
# 1. Programas Válidos e Construção da AST
# =====================================================================

def test_programa_minimo_valido():
    ast, parser = parse_code("programa vazio { } fim.")

    assert parser.errors == []
    assert not parser.had_lexical_error
    assert isinstance(ast, ProgramNode)
    assert ast.name == "vazio"
    assert isinstance(ast.block, BlockNode)
    assert ast.block.declarations == []
    assert ast.block.statements == []

def test_declaracoes_variaveis_com_e_sem_dois_pontos():
    codigo = """
    programa decls {
        var x inteiro;
        var y, z : inteiro;
        var flag1, flag2 booleano;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    assert ast is not None
    assert len(ast.block.declarations) == 3

    d1, d2, d3 = ast.block.declarations
    assert isinstance(d1, VarDeclNode)
    assert d1.names == ["x"]
    assert d1.var_type == DataType.INTEIRO

    assert d2.names == ["y", "z"]
    assert d2.var_type == DataType.INTEIRO

    assert d3.names == ["flag1", "flag2"]
    assert d3.var_type == DataType.BOOLEANO

def test_comandos_basicos_io_bloco_enquanto():
    codigo = """
    programa comandos {
        var x inteiro;
        leia x;
        leia (x);
        {
            var local inteiro;
            local = 5;
            escreva local;
        }
        enquanto (x > 0) {
            escreva x;
            x = x - 1;
        }
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    assert ast is not None
    stmts = ast.block.statements
    assert len(stmts) == 4
    assert isinstance(stmts[0], ReadNode) and stmts[0].name == "x"
    assert isinstance(stmts[1], ReadNode) and stmts[1].name == "x"
    assert isinstance(stmts[2], BlockNode) and len(stmts[2].declarations) == 1
    assert isinstance(stmts[3], WhileNode)

def test_extensao_d_para_e_repita():
    codigo = """
    programa ext_d {
        var i, x : inteiro;
        para i = 1 ate 10 {
            escreva i;
        }
        para i = 10 ate 0 passo -2
            escreva i;
        repita {
            leia x;
        } ate (x == 0);
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    assert ast is not None
    stmts = ast.block.statements
    assert len(stmts) == 3

    for1, for2, rep = stmts
    assert isinstance(for1, ForNode)
    assert for1.var_name == "i"
    assert for1.step is None
    assert isinstance(for1.body, BlockNode)

    assert isinstance(for2, ForNode)
    assert isinstance(for2.step, UnaryOpNode)
    assert for2.step.op == "-"
    assert isinstance(for2.body, WriteNode)

    assert isinstance(rep, RepeatNode)
    assert isinstance(rep.body, BlockNode)
    assert isinstance(rep.condition, BinOpNode)
    assert rep.condition.op == "=="

def test_coordenadas_linha_coluna_nos_ast():
    codigo = "programa pos {\n    var x inteiro;\n    x = 42;\n}\nfim."
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    assert ast is not None
    assert (ast.line, ast.column) == (1, 1)
    assert (ast.block.line, ast.block.column) == (1, 14)

    decl = ast.block.declarations[0]
    assert (decl.line, decl.column) == (2, 5)

    assign = ast.block.statements[0]
    assert isinstance(assign, AssignNode)
    assert (assign.line, assign.column) == (3, 5)
    assert isinstance(assign.expr, LiteralNode)
    assert (assign.expr.line, assign.expr.column) == (3, 9)

@pytest.mark.parametrize("fixture_path", VALID_FIXTURES, ids=lambda p: p.name)
def test_fixtures_validos_aceitos(fixture_path: Path):
    source = fixture_path.read_text(encoding="utf-8")
    ast, parser = parse_code(source)

    assert not parser.had_lexical_error
    assert parser.errors == []
    assert isinstance(ast, ProgramNode)


# =====================================================================
# 2. Precedência e Associatividade de Expressões
# =====================================================================

def test_precedencia_aritmetica_multiplicacao_antes_soma():
    ast, parser = parse_code(wrap_expr("2 + 3 * 4"))
    assert parser.errors == []
    assign = ast.block.statements[0]
    assert isinstance(assign, AssignNode)

    expr = assign.expr
    assert isinstance(expr, BinOpNode) and expr.op == "+"
    assert isinstance(expr.left, LiteralNode) and expr.left.value == 2
    assert isinstance(expr.right, BinOpNode) and expr.right.op == "*"
    assert expr.right.left.value == 3
    assert expr.right.right.value == 4

def test_parenteses_alteram_precedencia():
    ast, parser = parse_code(wrap_expr("(2 + 3) * 4"))
    assert parser.errors == []
    expr = ast.block.statements[0].expr

    assert isinstance(expr, BinOpNode) and expr.op == "*"
    assert isinstance(expr.left, BinOpNode) and expr.left.op == "+"
    assert expr.left.left.value == 2
    assert expr.left.right.value == 3
    assert isinstance(expr.right, LiteralNode) and expr.right.value == 4

def test_associatividade_esquerda_aditiva_e_multiplicativa():
    ast, parser = parse_code(wrap_expr("10 - 3 - 2"))
    assert parser.errors == []
    expr = ast.block.statements[0].expr
    assert isinstance(expr, BinOpNode) and expr.op == "-"
    assert isinstance(expr.left, BinOpNode) and expr.left.op == "-"
    assert expr.left.left.value == 10
    assert expr.left.right.value == 3
    assert expr.right.value == 2

    ast2, parser2 = parse_code(wrap_expr("12 / 3 * 2 % 5"))
    assert parser2.errors == []
    expr2 = ast2.block.statements[0].expr
    assert isinstance(expr2, BinOpNode) and expr2.op == "%"
    assert isinstance(expr2.left, BinOpNode) and expr2.left.op == "*"
    assert isinstance(expr2.left.left, BinOpNode) and expr2.left.left.op == "/"

def test_precedencia_unaria_relacional_e_logica():
    ast, parser = parse_code(wrap_expr("não falso e x + 1 > -2 * y ou z == 0"))
    assert parser.errors == []
    expr = ast.block.statements[0].expr

    # Top level: (...) ou (z == 0)
    assert isinstance(expr, BinOpNode) and expr.op == "ou"
    assert isinstance(expr.right, BinOpNode) and expr.right.op == "=="

    # Left of 'ou': (não falso) e ((x + 1) > ((-2) * y))
    left_and = expr.left
    assert isinstance(left_and, BinOpNode) and left_and.op == "e"
    assert isinstance(left_and.left, UnaryOpNode) and left_and.left.op == "não"
    assert isinstance(left_and.left.operand, LiteralNode)
    assert left_and.left.operand.value is False

    rel = left_and.right
    assert isinstance(rel, BinOpNode) and rel.op == ">"
    assert isinstance(rel.left, BinOpNode) and rel.left.op == "+"
    assert isinstance(rel.right, BinOpNode) and rel.right.op == "*"
    assert isinstance(rel.right.left, UnaryOpNode) and rel.right.left.op == "-"

def test_unario_encadeado_associativo_a_direita():
    ast, parser = parse_code(wrap_expr("não não verdadeiro"))
    assert parser.errors == []
    expr = ast.block.statements[0].expr
    assert isinstance(expr, UnaryOpNode) and expr.op == "não"
    assert isinstance(expr.operand, UnaryOpNode) and expr.operand.op == "não"
    assert isinstance(expr.operand.operand, LiteralNode)
    assert expr.operand.operand.value is True

def test_relacional_nao_associativo_rejeitado():
    ast, parser = parse_code(wrap_expr("1 < 2 < 3"))
    assert len(parser.errors) >= 1
    assert "[Erro Sintático]" in parser.errors[0]

# =====================================================================
# 3. Resolução do Dangling Else
# =====================================================================

def test_dangling_else_associa_ao_se_mais_proximo():
    codigo = """
    programa p {
        var a, b booleano;
        se (a)
            se (b)
                escreva 1;
            senão
                escreva 2;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    outer_if = ast.block.statements[0]
    assert isinstance(outer_if, IfNode)
    assert outer_if.else_branch is None

    inner_if = outer_if.then_branch
    assert isinstance(inner_if, IfNode)
    assert isinstance(inner_if.then_branch, WriteNode)
    assert isinstance(inner_if.else_branch, WriteNode)
    assert inner_if.then_branch.expr.value == 1
    assert inner_if.else_branch.expr.value == 2

def test_dangling_else_com_chaves_associa_ao_se_externo():
    codigo = """
    programa p {
        var a, b booleano;
        se (a) {
            se (b)
                escreva 1;
        } senão
            escreva 2;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    outer_if = ast.block.statements[0]
    assert isinstance(outer_if, IfNode)
    assert isinstance(outer_if.then_branch, BlockNode)
    inner_if = outer_if.then_branch.statements[0]
    assert isinstance(inner_if, IfNode)
    assert inner_if.else_branch is None
    assert isinstance(outer_if.else_branch, WriteNode)
    assert outer_if.else_branch.expr.value == 2

def test_dangling_else_triplo_aninhamento():
    codigo = """
    programa p {
        var a, b, c booleano;
        se (a)
            se (b)
                se (c)
                    escreva 1;
                senão
                    escreva 2;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert parser.errors == []
    if_a = ast.block.statements[0]
    assert isinstance(if_a, IfNode) and if_a.else_branch is None
    if_b = if_a.then_branch
    assert isinstance(if_b, IfNode) and if_b.else_branch is None
    if_c = if_b.then_branch
    assert isinstance(if_c, IfNode) and isinstance(if_c.else_branch, WriteNode)

# =====================================================================
# 4. PrintAstVisitor (Pretty Printer) e Padrão Visitor
# =====================================================================

def test_print_ast_visitor_formata_arvore_completa():
    codigo = """
    programa demo {
        var x, y : inteiro;
        x = 2 + 3 * 4;
        se (x > 10)
            escreva x;
        senão
            leia y;
        enquanto (x > 0)
            x = x - 1;
        para x = 1 ate 5 passo 2
            escreva x;
        repita
            x = x + 1;
        ate (x == 10);
    }
    fim.
    """
    ast, parser = parse_code(codigo)
    assert parser.errors == []

    printer = PrintAstVisitor()
    output = printer.format(ast)

    assert "Program(name='demo')" in output
    assert "VarDecl(names=['x', 'y'], type=INTEIRO)" in output
    assert "Assign(name='x')" in output
    assert "BinOp(op='+')" in output
    assert "BinOp(op='*')" in output
    assert "If" in output
    assert "else:" in output
    assert "Read(name='y')" in output
    assert "While" in output
    assert "For(var='x')" in output
    assert "step:" in output
    assert "Repeat" in output
    assert "until:" in output

def test_expr_node_suporta_anotacao_inferred_type():
    ast, parser = parse_code(wrap_expr("verdadeiro"))
    assert parser.errors == []
    lit = ast.block.statements[0].expr
    assert isinstance(lit, LiteralNode)
    assert lit.inferred_type is None

    lit.inferred_type = DataType.BOOLEANO
    output = PrintAstVisitor().format(ast)
    assert "Literal(verdadeiro, BOOLEANO) [BOOLEANO]" in output

# =====================================================================
# 5. Integração com TokenType.ERROR do Scanner
# =====================================================================

def test_parser_ignora_token_error_do_scanner_sem_travar(capsys):
    codigo = """
    programa erro_lexico {
        var x inteiro;
        x = 10 @;
        escreva x;
    }
    fim.
    """
    scanner = Scanner(codigo)
    parser = Parser(scanner)
    ast = parser.parse()
    captured = capsys.readouterr()

    assert parser.had_lexical_error is True
    assert "[Erro Léxico]" in captured.err
    assert parser.errors == []
    assert isinstance(ast, ProgramNode)
    assert len(ast.block.statements) == 2

def test_parser_nao_trava_quando_entrada_so_tem_erros_lexicos(capsys):
    scanner = Scanner("@@@ ! $")
    parser = Parser(scanner)
    ast = parser.parse()
    captured = capsys.readouterr()

    assert parser.had_lexical_error is True
    assert "[Erro Léxico]" in captured.err
    assert len(parser.errors) == 1
    assert "[Erro Sintático]" in parser.errors[0]
    assert ast is None

# =====================================================================
# 6. Recuperação em Modo Pânico e Erros Sintáticos com Posição
# =====================================================================

def test_recuperacao_multiplos_erros_em_uma_execucao():
    codigo = """
    programa erros {
        var x inteiro;
        x = ;
        y = 10
        escreva ;
        x = 5;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 3
    assert "Linha 4, Coluna 13" in parser.errors[0]
    assert "Linha 6, Coluna 9" in parser.errors[1]
    assert "Linha 6, Coluna 17" in parser.errors[2]
    assert all(err.startswith("[Erro Sintático]") for err in parser.errors)
    # Recuperou e ainda analisou 'x = 5;'
    assert ast is not None
    assert any(isinstance(stmt, AssignNode) and stmt.name == "x" for stmt in ast.block.statements)

def test_recuperacao_condicao_invalida_no_se_continua_no_bloco():
    codigo = """
    programa cond_err {
        var x, y : inteiro;
        se (x > ) {
            y = ;
        }
        x = 1;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 2
    assert "Linha 4," in parser.errors[0]
    assert "Linha 5," in parser.errors[1]
    assert ast is not None
    assert len(ast.block.statements) == 2

def test_recuperacao_then_com_erro_ainda_analisa_senao():
    codigo = """
    programa then_err {
        var x inteiro;
        se (x > 0)
            x = ;
        senão
            x = 2;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 1
    assert "Linha 5, Coluna 17" in parser.errors[0]
    assert ast is not None
    if_node = ast.block.statements[0]
    assert isinstance(if_node, IfNode)
    assert isinstance(if_node.else_branch, AssignNode)
    assert if_node.else_branch.name == "x"

def test_recuperacao_repita_corpo_com_erro_ainda_analisa_ate():
    codigo = """
    programa repita_err {
        var x inteiro;
        repita
            x = ;
        ate (x == 0);
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 1
    assert "Linha 5, Coluna 17" in parser.errors[0]
    assert ast is not None
    assert isinstance(ast.block.statements[0], RepeatNode)

def test_declaracao_apos_comando_reporta_erro_sem_loop_infinito():
    codigo = """
    programa var_tardia {
        var x inteiro;
        x = 1;
        var y inteiro;
        y = 2;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 1
    assert "[Erro Sintático] Linha 5, Coluna 9:" in parser.errors[0]
    assert ast is not None
    assert len(ast.block.statements) == 2

def test_senao_solto_reporta_erro_e_continua():
    codigo = """
    programa senao_solto {
        var x inteiro;
        senão x = 1;
        escreva x;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 1
    assert "Linha 4, Coluna 9" in parser.errors[0]
    assert ast is not None
    assert len(ast.block.statements) == 1
    assert isinstance(ast.block.statements[0], WriteNode)

def test_recuperacao_se_sem_ramo_then_antes_de_senao():
    codigo = """
    programa se_vazio {
        var a booleano;
        se (a)
        senão
            escreva 1;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) == 1
    assert "Linha 5, Coluna 9" in parser.errors[0]
    assert ast is not None
    if_node = ast.block.statements[0]
    assert isinstance(if_node, IfNode)
    assert isinstance(if_node.else_branch, WriteNode)

def test_recuperacao_para_faltando_ate_e_proximo_comando():
    codigo = """
    programa para_err {
        var i inteiro;
        para i = 1 10 {
            escreva i;
        }
        escreva 99;
    }
    fim.
    """
    ast, parser = parse_code(codigo)

    assert len(parser.errors) >= 1
    assert "esperado 'ate'" in parser.errors[0]
    assert ast is not None
    assert any(isinstance(s, WriteNode) for s in ast.block.statements)

@pytest.mark.parametrize(
    "codigo,trecho_esperado",
    [
        ("", "[Erro Sintático] Linha 1, Coluna 1: esperado 'programa', encontrado 'EOF'"),
        ("programa p { } fim", "esperado '.' após 'fim'"),
        ("programa p { }", "esperado 'fim'"),
        ("programa p { } fim. x = 1;", "esperado fim de arquivo (EOF)"),
        ("programa { } fim.", "esperado identificador"),
        ("programa p { var x real; } fim.", "esperado tipo"),
        ("programa p { leia 123; } fim.", "esperado identificador em 'leia'"),
    ],
)
def test_erros_estruturais_com_posicao(codigo: str, trecho_esperado: str):
    _, parser = parse_code(codigo)

    assert len(parser.errors) >= 1
    assert any(trecho_esperado in err for err in parser.errors)


@pytest.mark.parametrize("fixture_path", INVALID_SYNTAX_FIXTURES, ids=lambda p: p.name)
def test_fixtures_invalidos_rejeitados_com_posicao(fixture_path: Path):
    source = fixture_path.read_text(encoding="utf-8")
    _, parser = parse_code(source)

    assert len(parser.errors) >= 1
    assert all(
        err.startswith("[Erro Sintático] Linha ") and ", Coluna " in err
        for err in parser.errors
    )

# =====================================================================
# 7. CLI (main.py)
# =====================================================================

def test_cli_programa_valido_e_flag_ast(capsys):
    valid_file = str(FIXTURES_DIR / "valid" / "01_basico.ml")

    code = main([valid_file])
    captured = capsys.readouterr()
    assert code == 0
    assert "sem erros" in captured.out

    code_ast = main([valid_file, "--ast"])
    captured_ast = capsys.readouterr()
    assert code_ast == 0
    assert "Program(name='basico')" in captured_ast.out

def test_cli_programa_valido_flag_tokens(capsys):
    valid_file = str(FIXTURES_DIR / "valid" / "01_basico.ml")
    code = main([valid_file, "--tokens"])
    captured = capsys.readouterr()
    assert code == 0
    assert "TokenType.KEYWORD" in captured.out
    assert "TokenType.EOF" in captured.out

def test_cli_programa_invalido_retorna_codigo_1(capsys):
    invalid_file = str(FIXTURES_DIR / "invalid" / "sintatico_multiplos_erros.ml")
    code = main([invalid_file, "--ast"])
    captured = capsys.readouterr()

    assert code == 1
    assert "[Erro Sintático]" in captured.err
    assert "Program(" not in captured.out

def test_cli_arquivo_inexistente(capsys):
    code = main(["nao_existe.ml"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Arquivo não encontrado" in captured.err
