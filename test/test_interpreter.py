from pathlib import Path
import pytest
from main import main
from src.classes.ast_nodes import BinOpNode, LiteralNode, ProgramNode
from src.classes.interpreter import ExecutionError, Interpreter
from src.classes.optimizer import ConstantFolder
from src.classes.parser import Parser
from src.classes.scanner import Scanner
from src.classes.semantic import SemanticAnalyzer
from src.enum.data_type import DataType

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURES = sorted((FIXTURES_DIR / "valid").glob("*.ml"))
INVALID_RUNTIME_FIXTURES = sorted((FIXTURES_DIR / "invalid").glob("execucao_*.ml"))

def execute_code(
    source: str,
    inputs: list[str] | None = None,
    max_steps: int | None = None,
    optimize: bool = False,
) -> tuple[Interpreter, list[str]]:
    scanner = Scanner(source)
    parser = Parser(scanner, emit_errors=False)
    ast = parser.parse()
    assert ast is not None
    assert parser.errors == []

    analyzer = SemanticAnalyzer(emit_errors=False)
    semantic_ok = analyzer.analyze(ast)
    assert semantic_ok is True
    assert analyzer.errors == []

    if optimize:
        optimizer = ConstantFolder()
        ast = optimizer.optimize(ast)

    input_list = list(inputs or [])

    def mock_input(prompt: str = "") -> str:
        if not input_list:
            raise EOFError("Sem mais entradas disponíveis")
        return input_list.pop(0)

    output_list: list[str] = []

    def mock_output(text: str) -> None:
        output_list.append(text)

    interpreter = Interpreter(
        input_fn=mock_input,
        output_fn=mock_output,
        max_steps=max_steps,
        emit_errors=False,
    )
    interpreter.interpret(ast)
    return interpreter, output_list

# 1. Operações Aritméticas e Divisão Inteira
def test_operacoes_aritmeticas_basicas():
    codigo = """
    programa aritmetica {
        var a, b, c, d, r : inteiro;
        a = 10 + 20;
        b = 50 - 15;
        c = 6 * 7;
        d = 100 / 4;
        r = 17 % 5;
        escreva a;
        escreva b;
        escreva c;
        escreva d;
        escreva r;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["30", "35", "42", "25", "2"]

def test_divisao_inteira_trunca():
    codigo = """
    programa div_inteira {
        var x inteiro;
        x = 7 / 2;
        escreva x;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["3"]

def test_divisao_por_zero_lanca_erro_de_execucao():
    codigo = """
    programa div_zero {
        var x, y : inteiro;
        x = 10;
        y = 0;
        escreva x / y;
    }
    fim.
    """
    interpreter, _ = execute_code(codigo)
    assert len(interpreter.errors) == 1
    assert "[Erro de Execução]" in interpreter.errors[0]
    assert "divisão por zero" in interpreter.errors[0]
    assert "Linha 6" in interpreter.errors[0]

def test_modulo_por_zero_lanca_erro_de_execucao():
    codigo = """
    programa mod_zero {
        var x, y : inteiro;
        x = 10;
        y = 0;
        escreva x % y;
    }
    fim.
    """
    interpreter, _ = execute_code(codigo)
    assert len(interpreter.errors) == 1
    assert "[Erro de Execução]" in interpreter.errors[0]
    assert "divisão por zero no operador '%'" in interpreter.errors[0]

# 2. Operações Relacionais e Lógicas com Curto-Circuito
def test_operadores_relacionais():
    codigo = """
    programa rel {
        var eq, ne, lt, le, gt, ge : booleano;
        eq = 10 == 10;
        ne = 10 != 5;
        lt = 3 < 7;
        le = 5 <= 5;
        gt = 8 > 12;
        ge = 4 >= 4;
        escreva eq;
        escreva ne;
        escreva lt;
        escreva le;
        escreva gt;
        escreva ge;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == [
        "verdadeiro",
        "verdadeiro",
        "verdadeiro",
        "verdadeiro",
        "falso",
        "verdadeiro",
    ]

def test_curto_circuito_operador_e():
    # Se o operador 'e' não tivesse curto-circuito, 10 / 0 causaria erro em runtime
    codigo = """
    programa curto_circuito_e {
        var res booleano;
        res = falso e (10 / 0 == 0);
        escreva res;
    }
    fim.
    """
    interpreter, outputs = execute_code(codigo)
    assert interpreter.errors == []
    assert outputs == ["falso"]

def test_curto_circuito_operador_ou():
    # Se o operador 'ou' não tivesse curto-circuito, 10 / 0 causaria erro em runtime
    codigo = """
    programa curto_circuito_ou {
        var res booleano;
        res = verdadeiro ou (10 / 0 == 0);
        escreva res;
    }
    fim.
    """
    interpreter, outputs = execute_code(codigo)
    assert interpreter.errors == []
    assert outputs == ["verdadeiro"]


def test_operador_unario_negativo_e_nao():
    codigo = """
    programa unarios {
        var x inteiro;
        var b1, b2 : booleano;
        x = -15;
        b1 = não falso;
        b2 = não verdadeiro;
        escreva x;
        escreva b1;
        escreva b2;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["-15", "verdadeiro", "falso"]

# 3. Escopo, Shadowing e Variáveis em Blocos Aninhados
def test_escopo_aninhado_e_shadowing_em_runtime():
    codigo = """
    programa escopo {
        var x inteiro;
        x = 10;
        {
            var x inteiro;
            x = 20;
            escreva x;
        }
        escreva x;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["20", "10"]

def test_modificacao_de_variavel_do_escopo_externo():
    codigo = """
    programa externo {
        var x inteiro;
        x = 1;
        {
            x = 99;
        }
        escreva x;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["99"]

# 4. Estruturas de Controle de Fluxo (se, enquanto)
def test_condicional_se_e_senao():
    codigo = """
    programa cond {
        var x inteiro;
        x = 10;
        se (x > 5) {
            escreva 1;
        } senão {
            escreva 0;
        }

        se (x < 5) {
            escreva 2;
        } senão {
            escreva 3;
        }
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["1", "3"]

def test_laco_enquanto():
    codigo = """
    programa loop_enquanto {
        var contador, total : inteiro;
        contador = 1;
        total = 0;
        enquanto (contador <= 4) {
            total = total + contador;
            contador = contador + 1;
        }
        escreva total;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["10"]

# 5. Extensão Obrigatória (Opção D: para e repita/ate)
def test_laco_para_crescente_e_passo_padrao():
    codigo = """
    programa loop_para {
        var i, soma : inteiro;
        soma = 0;
        para i = 1 ate 5 {
            soma = soma + i;
        }
        escreva soma;
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["15"]

def test_laco_para_com_passo_customizado_e_decrescente():
    codigo = """
    programa loop_para_passo {
        var i : inteiro;
        para i = 10 ate 4 passo -2 {
            escreva i;
        }
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["10", "8", "6", "4"]

def test_laco_para_passo_zero_dispara_erro_execucao():
    codigo = """
    programa passo_zero {
        var i inteiro;
        para i = 1 ate 5 passo 0 {
            escreva i;
        }
    }
    fim.
    """
    interpreter, _ = execute_code(codigo)
    assert len(interpreter.errors) == 1
    assert "[Erro de Execução]" in interpreter.errors[0]
    assert "passo do laço 'para' não pode ser zero" in interpreter.errors[0]

def test_laco_repita_ate_executa_ao_menos_uma_vez():
    codigo = """
    programa repita_once {
        var x inteiro;
        x = 0;
        repita {
            x = x + 1;
            escreva x;
        } ate (verdadeiro);
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["1"]

def test_laco_repita_ate_loop_multiplas_vezes():
    codigo = """
    programa repita_multiplo {
        var cont inteiro;
        cont = 3;
        repita {
            escreva cont;
            cont = cont - 1;
        } ate (cont == 0);
    }
    fim.
    """
    _, outputs = execute_code(codigo)
    assert outputs == ["3", "2", "1"]

# 6. Runtime I/O (leia / escreva) e Formatação de Tipos
def test_leia_inteiro_e_booleano_com_sucesso():
    codigo = """
    programa io_sucesso {
        var num inteiro;
        var flag booleano;
        leia num;
        leia flag;
        escreva num * 2;
        escreva flag;
    }
    fim.
    """
    _, outputs = execute_code(codigo, inputs=["21", "verdadeiro"])
    assert outputs == ["42", "verdadeiro"]

def test_leia_inteiro_com_entrada_invalida_lanca_erro():
    codigo = """
    programa io_err_int {
        var n inteiro;
        leia n;
    }
    fim.
    """
    interpreter, _ = execute_code(codigo, inputs=["abc"])
    assert len(interpreter.errors) == 1
    assert "[Erro de Execução]" in interpreter.errors[0]
    assert "entrada inválida para variável inteira 'n'" in interpreter.errors[0]

def test_leia_booleano_com_entrada_invalida_lanca_erro():
    codigo = """
    programa io_err_bool {
        var b booleano;
        leia b;
    }
    fim.
    """
    interpreter, _ = execute_code(codigo, inputs=["talvez"])
    assert len(interpreter.errors) == 1
    assert "[Erro de Execução]" in interpreter.errors[0]
    assert "entrada inválida para variável booleana 'b'" in interpreter.errors[0]

def test_leia_com_eof_lanca_erro_execucao():
    codigo = """
    programa io_eof {
        var x inteiro;
        leia x;
    }
    fim.
    """
    interpreter, _ = execute_code(codigo, inputs=[])
    assert len(interpreter.errors) == 1
    assert "fim inesperado da entrada (EOF)" in interpreter.errors[0]

def test_limite_de_passos_max_steps_evita_loop_infinito():
    codigo = """
    programa loop_infinito {
        var x inteiro;
        x = 0;
        enquanto (verdadeiro) {
            x = x + 1;
        }
    }
    fim.
    """
    interpreter, _ = execute_code(codigo, max_steps=100)
    assert len(interpreter.errors) == 1
    assert "[Erro de Execução]" in interpreter.errors[0]
    assert "limite máximo de passos (100) excedido" in interpreter.errors[0]

# 7. Otimização por Constant Folding (optimizer.py)
def test_constant_folding_aritmetico_e_unario():
    codigo = """
    programa opt_arit {
        var x inteiro;
        x = 2 + 3 * 4 - -5;
        escreva x;
    }
    fim.
    """
    scanner = Scanner(codigo)
    ast = Parser(scanner).parse()
    SemanticAnalyzer().analyze(ast)

    optimizer = ConstantFolder()
    opt_ast = optimizer.optimize(ast)

    # Verifica na AST que a expressão foi reduzida a um único LiteralNode(19)
    assign = opt_ast.block.statements[0]
    assert isinstance(assign.expr, LiteralNode)
    assert assign.expr.value == 19
    assert assign.expr.inferred_type == DataType.INTEIRO

    # Execução da AST otimizada produz o mesmo resultado
    interpreter = Interpreter(output_fn=lambda t: None)
    assert interpreter.interpret(opt_ast) is True

def test_constant_folding_relacional_e_logico():
    codigo = """
    programa opt_logico {
        var b1, b2, b3 : booleano;
        b1 = 10 > 5 e não falso;
        b2 = verdadeiro ou falso;
        b3 = 4 != 4;
    }
    fim.
    """
    scanner = Scanner(codigo)
    ast = Parser(scanner).parse()
    SemanticAnalyzer().analyze(ast)

    opt_ast = ConstantFolder().optimize(ast)
    stmts = opt_ast.block.statements
    assert isinstance(stmts[0].expr, LiteralNode) and stmts[0].expr.value is True
    assert isinstance(stmts[1].expr, LiteralNode) and stmts[1].expr.value is True
    assert isinstance(stmts[2].expr, LiteralNode) and stmts[2].expr.value is False

def test_constant_folding_simplifica_desvios_condicionais():
    codigo = """
    programa opt_if {
        var x inteiro;
        se (verdadeiro) {
            x = 10;
        } senão {
            x = 20;
        }
    }
    fim.
    """
    scanner = Scanner(codigo)
    ast = Parser(scanner).parse()
    SemanticAnalyzer().analyze(ast)

    opt_ast = ConstantFolder().optimize(ast)
    if_node = opt_ast.block.statements[0]
    # O ramo 'senão' tornou-se None (código morto eliminado)
    assert if_node.else_branch is None

def test_constant_folding_nao_dobra_divisao_por_zero_em_tempo_de_compilacao():
    codigo = """
    programa opt_div_zero {
        var x inteiro;
        x = 10 / 0;
    }
    fim.
    """
    scanner = Scanner(codigo)
    ast = Parser(scanner).parse()
    SemanticAnalyzer().analyze(ast)

    opt_ast = ConstantFolder().optimize(ast)
    assign = opt_ast.block.statements[0]
    # Não dobrou para Literal, preservou BinOpNode para que o runtime reporte o erro
    assert isinstance(assign.expr, BinOpNode)
    assert assign.expr.op == "/"

# 8. Execução Ponta a Ponta de Todos os Fixtures Válidos
@pytest.mark.parametrize("fixture_path", VALID_FIXTURES, ids=lambda p: p.name)
def test_execucao_fixtures_validos_com_e_sem_otimizacao(fixture_path: Path):
    source = fixture_path.read_text(encoding="utf-8")
    # Fornece entradas genéricas caso o fixture contenha comandos leia
    inputs = ["10", "20", "30", "verdadeiro", "0"]

    # Execução normal
    interp_normal, _ = execute_code(source, inputs=list(inputs), optimize=False)
    assert interp_normal.errors == []

    # Execução com Constant Folding
    interp_opt, _ = execute_code(source, inputs=list(inputs), optimize=True)
    assert interp_opt.errors == []

# 9. Integração com a CLI (main.py)
def test_cli_executa_programa_com_saida(capsys):
    file_path = str(FIXTURES_DIR / "valid" / "02_dangling_else.ml")
    code = main([file_path])
    captured = capsys.readouterr()

    assert code == 0
    assert "2\n" in captured.out
    assert "Programa executado com sucesso" in captured.out

def test_cli_executa_com_flag_opt(capsys):
    file_path = str(FIXTURES_DIR / "valid" / "03_lacos_blocos.ml")
    code = main([file_path, "--opt"])
    captured = capsys.readouterr()

    assert code == 0
    assert "15\n" in captured.out
    assert "Programa executado com sucesso" in captured.out

def test_cli_comparacao_ast_antes_e_depois_constant_folding(capsys):
    file_path = str(FIXTURES_DIR / "valid" / "05_precedencia.ml")
    code = main([file_path, "--opt", "--dump-ast"])
    captured = capsys.readouterr()

    assert code == 0
    assert "=== AST Original ===" in captured.out
    assert "=== AST Otimizada (Constant Folding) ===" in captured.out

def test_cli_erro_de_execucao_retorna_codigo_1(capsys):
    file_path = str(FIXTURES_DIR / "invalid" / "execucao_divisao_por_zero.ml")
    code = main([file_path])
    captured = capsys.readouterr()

    assert code == 1
    assert "[Erro de Execução]" in captured.err
    assert "divisão por zero" in captured.err

def test_cli_limite_max_steps_via_argumento(capsys):
    file_path = str(FIXTURES_DIR / "valid" / "03_lacos_blocos.ml")
    # Força limite de passos muito baixo para acionar interrupção
    code = main([file_path, "--max-steps", "2"])
    captured = capsys.readouterr()

    assert code == 1
    assert "[Erro de Execução]" in captured.err
    assert "limite máximo de passos (2) excedido" in captured.err
