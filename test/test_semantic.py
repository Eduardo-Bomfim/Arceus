from pathlib import Path
import pytest
from main import main
from src.classes.ast_nodes import AssignNode, BinOpNode, ProgramNode, UnaryOpNode, VarNode
from src.classes.parser import Parser
from src.classes.scanner import Scanner
from src.classes.semantic import SemanticAnalyzer
from src.classes.symbol_table import Symbol, SymbolTable
from src.classes.visitors.printer import PrintAstVisitor
from src.enum.data_type import DataType

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURES = sorted((FIXTURES_DIR / "valid").glob("*.ml"))
INVALID_SEMANTIC_FIXTURES = sorted((FIXTURES_DIR / "invalid").glob("semantico_*.ml"))

def analyze_code(
    source: str, emit_errors: bool = False
) -> tuple[ProgramNode, SemanticAnalyzer]:
    scanner = Scanner(source)
    parser = Parser(scanner, emit_errors=False)
    ast = parser.parse()
    assert not parser.had_lexical_error
    assert parser.errors == []
    assert isinstance(ast, ProgramNode)

    analyzer = SemanticAnalyzer(emit_errors=emit_errors)
    analyzer.analyze(ast)
    return ast, analyzer

# 1. Tabela de Símbolos e Gestão de Escopos
def test_symbol_table_escopos_aninhados_e_shadowing():
    table = SymbolTable()
    table.enter_scope()  # escopo 0

    sym_outer = Symbol("x", DataType.INTEIRO, line=2, column=5)
    assert table.declare(sym_outer) is True
    assert sym_outer.scope_level == 0
    assert table.lookup_local("x") is sym_outer
    assert table.lookup("x") is sym_outer

    # Redeclaração no mesmo escopo deve falhar
    assert table.declare(Symbol("x", DataType.BOOLEANO, line=3, column=5)) is False

    table.enter_scope()  # escopo 1
    assert table.lookup_local("x") is None
    assert table.lookup("x") is sym_outer

    # Shadowing em escopo interno é permitido
    sym_inner = Symbol("x", DataType.BOOLEANO, line=5, column=9)
    assert table.declare(sym_inner) is True
    assert sym_inner.scope_level == 1
    assert table.lookup("x") is sym_inner
    assert table.lookup_local("x") is sym_inner

    table.exit_scope()
    assert table.lookup("x") is sym_outer

    table.exit_scope()
    assert table.lookup("x") is None
    assert len(table.all_symbols) == 2

def test_symbol_table_exit_scope_vazio_dispara_erro():
    table = SymbolTable()
    with pytest.raises(RuntimeError):
        table.exit_scope()

# 2. Programas Válidos, Escopos e Anotação da AST
@pytest.mark.parametrize("fixture_path", VALID_FIXTURES, ids=lambda p: p.name)
def test_fixtures_validos_passam_no_semantico(fixture_path: Path):
    source = fixture_path.read_text(encoding="utf-8")
    _, analyzer = analyze_code(source)
    assert analyzer.errors == []

def test_anotacao_inferred_type_na_ast_e_pretty_printer():
    codigo = """
    programa anotacao {
        var x, y : inteiro;
        var ok booleano;
        x = -5 + 10 * 2;
        y = x;
        ok = (x >= y) e não falso;
    }
    fim.
    """
    ast, analyzer = analyze_code(codigo)
    assert analyzer.errors == []

    assign_x, assign_y, assign_ok = ast.block.statements
    assert isinstance(assign_x, AssignNode)
    assert isinstance(assign_x.expr, BinOpNode)
    assert assign_x.expr.inferred_type == DataType.INTEIRO
    assert isinstance(assign_x.expr.left, UnaryOpNode)
    assert assign_x.expr.left.inferred_type == DataType.INTEIRO

    assert isinstance(assign_y, AssignNode)
    assert isinstance(assign_y.expr, VarNode)
    assert assign_y.expr.inferred_type == DataType.INTEIRO

    assert isinstance(assign_ok, AssignNode)
    assert isinstance(assign_ok.expr, BinOpNode)
    assert assign_ok.expr.inferred_type == DataType.BOOLEANO
    assert assign_ok.expr.left.inferred_type == DataType.BOOLEANO
    assert assign_ok.expr.right.inferred_type == DataType.BOOLEANO

    printed = PrintAstVisitor().format(ast)
    assert "[INTEIRO]" in printed
    assert "[BOOLEANO]" in printed

def test_shadowing_valido_entre_escopos_e_isolamento_de_variavel_local():
    codigo = """
    programa escopos {
        var x inteiro;
        x = 10;
        {
            var x booleano;
            var local inteiro;
            x = verdadeiro;
            local = 5;
            se (x) {
                escreva local;
            }
        }
        x = x + 1;
        escreva x;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert analyzer.errors == []

def test_igualdade_e_desigualdade_aceitam_ambos_os_tipos_quando_iguais():
    codigo = """
    programa igualdade {
        var a, b : inteiro;
        var p, q, r : booleano;
        a = 1;
        b = 2;
        p = a == b;
        q = p != verdadeiro;
        r = p == q;
        escreva r;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert analyzer.errors == []

# 3. Variável Não Declarada, Redeclaração e Escopo
def test_variavel_nao_declarada_em_expressao_atribuicao_e_leia():
    codigo = """
    programa nao_declarada {
        var x inteiro;
        x = a + 1;
        b = 2;
        leia c;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert len(analyzer.errors) == 3
    assert "Linha 4, Coluna 13" in analyzer.errors[0]
    assert "'a'" in analyzer.errors[0]
    assert "Linha 5, Coluna 9" in analyzer.errors[1]
    assert "'b'" in analyzer.errors[1]
    assert "Linha 6, Coluna 9" in analyzer.errors[2]
    assert "'c'" in analyzer.errors[2]


def test_redeclaracao_mesmo_escopo_e_na_mesma_linha():
    codigo = """
    programa redecl {
        var x, x : inteiro;
        var y inteiro;
        var y booleano;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert len(analyzer.errors) == 2
    assert "'x' já declarada" in analyzer.errors[0]
    assert "'y' já declarada" in analyzer.errors[1]


def test_variavel_local_fora_do_escopo_reporta_erro():
    codigo = """
    programa fora_escopo {
        {
            var local inteiro;
            local = 10;
        }
        escreva local;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert len(analyzer.errors) == 1
    assert "Linha 7, Coluna 17" in analyzer.errors[0]
    assert "'local' não declarada" in analyzer.errors[0]

# 4. Checagem de Tipos, Operadores e Sentinela DataType.ERROR
@pytest.mark.parametrize(
    "corpo,trecho_esperado",
    [
        ("x = verdadeiro;", "incompatibilidade de tipos na atribuição"),
        ("ok = 10;", "incompatibilidade de tipos na atribuição"),
        ("x = 1 + verdadeiro;", "operador aritmético '+' exige operandos do tipo INTEIRO"),
        ("x = falso * 2;", "operador aritmético '*' exige operandos do tipo INTEIRO"),
        ("x = -verdadeiro;", "operador unário '-' exige operando do tipo INTEIRO"),
        ("ok = verdadeiro < 10;", "operador relacional '<' exige operandos do tipo INTEIRO"),
        ("ok = 10 == falso;", "operador relacional '==' exige operandos do mesmo tipo"),
        ("ok = 10 != verdadeiro;", "operador relacional '!=' exige operandos do mesmo tipo"),
        ("ok = 1 e verdadeiro;", "operador lógico 'e' exige operandos do tipo BOOLEANO"),
        ("ok = verdadeiro ou 0;", "operador lógico 'ou' exige operandos do tipo BOOLEANO"),
        ("ok = não 10;", "operador lógico 'não' exige operando do tipo BOOLEANO"),
        ("se (10) { escreva 1; }", "condição do comando 'se' deve ser do tipo BOOLEANO"),
        ("enquanto (x) { escreva 1; }", "condição do comando 'enquanto' deve ser do tipo BOOLEANO"),
        ("repita { escreva 1; } ate (x);", "condição do comando 'repita/ate' deve ser do tipo BOOLEANO"),
    ],
)
def test_erros_de_tipo_em_operadores_atribuicoes_e_condicoes(
    corpo: str, trecho_esperado: str
):
    codigo = f"""
    programa tipos {{
        var x inteiro;
        var ok booleano;
        x = 1;
        ok = verdadeiro;
        {corpo}
    }}
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert len(analyzer.errors) == 1
    assert analyzer.errors[0].startswith("[Erro Semântico]")
    assert trecho_esperado in analyzer.errors[0]

def test_extensao_d_para_valida_tipos_de_controle_limites_e_passo():
    codigo = """
    programa para_tipos {
        var b booleano;
        var i inteiro;
        para b = 1 ate 5 {
            escreva 1;
        }
        para i = verdadeiro ate falso passo verdadeiro {
            escreva i;
        }
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert len(analyzer.errors) == 4
    assert "variável de controle 'b'" in analyzer.errors[0]
    assert "expressão inicial" in analyzer.errors[1]
    assert "expressão final" in analyzer.errors[2]
    assert "expressão de passo" in analyzer.errors[3]

def test_sentinela_error_evita_cascata_de_erros_na_mesma_expressao():
    codigo = """
    programa sentinela {
        var x inteiro;
        x = nao_existe + 1 * 2 - 3;
        se (nao_existe + 1) {
            escreva x;
        }
    }
    fim.
    """
    ast, analyzer = analyze_code(codigo)
    # Apenas 2 erros: um para cada uso de 'nao_existe', sem cascata em '+', '*', '-', '=' ou 'se'
    assert len(analyzer.errors) == 2
    assert all("'nao_existe' não declarada" in err for err in analyzer.errors)

    assign_x = ast.block.statements[0]
    assert isinstance(assign_x, AssignNode)
    assert assign_x.expr.inferred_type == DataType.ERROR

# 5. Detecção de Variável Não Inicializada (Bônus Semântico)
def test_variavel_lida_antes_de_inicializacao_e_auto_atribuicao():
    codigo = """
    programa nao_init {
        var x, y : inteiro;
        escreva x;
        y = y + 1;
        escreva y;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert len(analyzer.errors) == 2
    assert "Linha 4, Coluna 17" in analyzer.errors[0]
    assert "'x' usada antes de ser inicializada" in analyzer.errors[0]
    assert "Linha 5, Coluna 13" in analyzer.errors[1]
    assert "'y' usada antes de ser inicializada" in analyzer.errors[1]

def test_leia_marca_variavel_como_inicializada():
    codigo = """
    programa init_leia {
        var x inteiro;
        leia x;
        escreva x + 1;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    assert analyzer.errors == []

def test_inicializacao_condicional_exige_ambos_os_ramos_then_e_else():
    codigo_valido = """
    programa cond_ok {
        var x inteiro;
        var c booleano;
        c = verdadeiro;
        se (c) {
            x = 1;
        } senão {
            x = 2;
        }
        escreva x;
    }
    fim.
    """
    _, analyzer_ok = analyze_code(codigo_valido)
    assert analyzer_ok.errors == []

    codigo_so_then = """
    programa cond_so_then {
        var x inteiro;
        var c booleano;
        c = verdadeiro;
        se (c) {
            x = 1;
        } senão {
            escreva 0;
        }
        escreva x;
    }
    fim.
    """
    _, analyzer_then = analyze_code(codigo_so_then)
    assert len(analyzer_then.errors) == 1
    assert "'x' usada antes de ser inicializada" in analyzer_then.errors[0]

    codigo_sem_else = """
    programa cond_sem_else {
        var x inteiro;
        var c booleano;
        c = verdadeiro;
        se (c) {
            x = 1;
        }
        escreva x;
    }
    fim.
    """
    _, analyzer_sem_else = analyze_code(codigo_sem_else)
    assert len(analyzer_sem_else.errors) == 1
    assert "'x' usada antes de ser inicializada" in analyzer_sem_else.errors[0]

def test_inicializacao_em_lacos_enquanto_para_e_repita():
    codigo = """
    programa lacos_init {
        var i, a, b, c : inteiro;
        var cond booleano;
        cond = verdadeiro;

        enquanto (cond) {
            a = 1;
        }
        escreva a;

        para i = 1 ate 3 {
            b = i;
        }
        escreva i;
        escreva b;

        repita {
            leia c;
        } ate (c == 0);
        escreva c;
    }
    fim.
    """
    _, analyzer = analyze_code(codigo)
    # 'a' (só em enquanto) e 'b' (só no corpo de para) não são garantidamente inicializadas;
    # 'i' (controle de para) e 'c' (corpo obrigatório de repita) SÃO inicializadas!
    assert len(analyzer.errors) == 2
    assert "'a' usada antes de ser inicializada" in analyzer.errors[0]
    assert "'b' usada antes de ser inicializada" in analyzer.errors[1]

# 6. Fixtures Inválidos e Integração CLI (main.py)
@pytest.mark.parametrize(
    "fixture_path", INVALID_SEMANTIC_FIXTURES, ids=lambda p: p.name
)
def test_fixtures_semanticos_invalidos_rejeitados_com_posicao(fixture_path: Path):
    source = fixture_path.read_text(encoding="utf-8")
    _, analyzer = analyze_code(source)

    assert len(analyzer.errors) >= 1
    assert all(
        err.startswith("[Erro Semântico] Linha ") and ", Coluna " in err
        for err in analyzer.errors
    )

def test_cli_ast_anotada_e_flag_symbols(capsys):
    valid_file = str(FIXTURES_DIR / "valid" / "01_basico.ml")

    code_ast = main([valid_file, "--ast"])
    out_ast = capsys.readouterr().out
    assert code_ast == 0
    assert "[INTEIRO]" in out_ast
    assert "[BOOLEANO]" in out_ast

    code_sym = main([valid_file, "--symbols"])
    out_sym = capsys.readouterr().out
    assert code_sym == 0
    assert "Nome | Tipo | Escopo | Linha | Coluna | Inicializada" in out_sym
    assert "x | INTEIRO | 0 |" in out_sym
    assert "ativo | BOOLEANO | 0 |" in out_sym

def test_cli_erro_semantico_retorna_codigo_1(capsys):
    invalid_file = str(FIXTURES_DIR / "invalid" / "semantico_tipos_incompativeis.ml")
    code = main([invalid_file, "--ast"])
    captured = capsys.readouterr()

    assert code == 1
    assert "[Erro Semântico]" in captured.err
    assert "Program(" not in captured.out
