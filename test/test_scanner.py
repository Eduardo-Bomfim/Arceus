from src.classes.scanner import Scanner
from src.enum.token_type import TokenType

def test_todas_palavras_reservadas():
    palavras = [
        "programa",
        "var",
        "inteiro",
        "booleano",
        "se",
        "senão",
        "enquanto",
        "escreva",
        "leia",
        "verdadeiro",
        "falso",
        "e",
        "ou",
        "não",
        "fim"
    ]

    scanner = Scanner(" ".join(palavras))

    for palavra in palavras:
        token = scanner.get_next_token()

        if palavra in {"e", "ou", "não"}:
            assert token.type == TokenType.OP_LOGICO
        else:
            assert token.type == TokenType.KEYWORD

        assert token.value == palavra

def test_identificadores_validos():
    codigo = "x idade cliente_1 usuario123"
    scanner = Scanner(codigo)
    identificadores = [
        "x",
        "idade",
        "cliente_1",
        "usuario123"
    ]

    for identificador in identificadores:
        token = scanner.get_next_token()

        assert token.type == TokenType.ID
        assert token.value == identificador

def test_identificador_nao_pode_comecar_com_sublinhado(): 
    scanner = Scanner("_nome") 
    token = scanner.get_next_token() 

    assert token.type == TokenType.ERROR 
    assert token.value == "_"

def test_identificador_nao_deve_ser_palavra_reservada():
    scanner = Scanner("var programa inteiro booleano")

    for palavra in ["var", "programa", "inteiro", "booleano"]:
        token = scanner.get_next_token()

        assert token.type == TokenType.KEYWORD
        assert token.value == palavra

def test_numeros_inteiros():
    scanner = Scanner("0 1 10 123 99999")
    numeros = ["0", "1", "10", "123", "99999"]

    for numero in numeros:
        token = scanner.get_next_token()

        assert token.type == TokenType.INT
        assert token.value == numero

def test_operadores_aritmeticos():
    scanner = Scanner("+ - * / %")
    operadores = ["+", "-", "*", "/", "%"]

    for operador in operadores:
        token = scanner.get_next_token()

        assert token.type == TokenType.OP_ARIT
        assert token.value == operador

def test_operadores_logicos():
    scanner = Scanner("e ou não")
    operadores = ["e", "ou", "não"]

    for operador in operadores:
        token = scanner.get_next_token()

        assert token.type == TokenType.OP_LOGICO
        assert token.value == operador

def test_operador_atribuicao():
    scanner = Scanner("=")
    token = scanner.get_next_token()

    assert token.type == TokenType.ASSIGN
    assert token.value == "="

def test_operadores_relacionais():
    scanner = Scanner("== != < <= > >=")
    operadores = ["==", "!=", "<", "<=", ">", ">="]

    for operador in operadores:
        token = scanner.get_next_token()

        assert token.type == TokenType.OP_REL
        assert token.value == operador

def test_lookahead_igualdade_vs_atribuicao():
    scanner = Scanner("= ==")

    token = scanner.get_next_token()
    assert token.type == TokenType.ASSIGN
    assert token.value == "="

    token = scanner.get_next_token()
    assert token.type == TokenType.OP_REL
    assert token.value == "=="

def test_lookahead_menor_vs_menor_igual():
    scanner = Scanner("< <=")

    token = scanner.get_next_token()
    assert token.type == TokenType.OP_REL
    assert token.value == "<"

    token = scanner.get_next_token()
    assert token.type == TokenType.OP_REL
    assert token.value == "<="

def test_lookahead_maior_vs_maior_igual():
    scanner = Scanner("> >=")

    token = scanner.get_next_token()
    assert token.type == TokenType.OP_REL
    assert token.value == ">"

    token = scanner.get_next_token()
    assert token.type == TokenType.OP_REL
    assert token.value == ">="

def test_lookahead_diferente():
    scanner = Scanner("!=")
    token = scanner.get_next_token()

    assert token.type == TokenType.OP_REL
    assert token.value == "!="

def test_delimitadores():
    scanner = Scanner("( ) { } ; : , .")
    delimitadores = [
        "(",
        ")",
        "{",
        "}",
        ";",
        ":",
        ",",
        "."
    ]

    for delimitador in delimitadores:
        token = scanner.get_next_token()

        assert token.type == TokenType.DELIM
        assert token.value == delimitador

def test_ignorar_espacos():
    scanner = Scanner("   var     x     inteiro   ")

    token = scanner.get_next_token()
    assert token.type == TokenType.KEYWORD
    assert token.value == "var"

    token = scanner.get_next_token()
    assert token.type == TokenType.ID
    assert token.value == "x"

    token = scanner.get_next_token()
    assert token.type == TokenType.KEYWORD
    assert token.value == "inteiro"

def test_ignorar_quebras_de_linha():
    scanner = Scanner("var\n\nx\ninteiro")

    token = scanner.get_next_token()
    assert token.value == "var"

    token = scanner.get_next_token()
    assert token.value == "x"

    token = scanner.get_next_token()
    assert token.value == "inteiro"

def test_ignorar_comentario():
    codigo = """
    # Este comentário deve ser ignorado
    var x inteiro;
    """
    scanner = Scanner(codigo)
    token = scanner.get_next_token()

    assert token.type == TokenType.KEYWORD
    assert token.value == "var"

def test_comentario_no_final_da_linha():
    codigo = "var x inteiro; # comentário\nescreva x;"
    scanner = Scanner(codigo)
    valores = []

    while True:
        token = scanner.get_next_token()

        if token.type == TokenType.EOF:
            break

        valores.append(token.value)

    assert valores == [
        "var",
        "x",
        "inteiro",
        ";",
        "escreva",
        "x",
        ";"
    ]

def test_multiplos_comentarios():
    codigo = """
    # comentário 1
    var x inteiro;
    # comentário 2
    x = 10;
    # comentário 3
    """

    scanner = Scanner(codigo)
    valores = []

    while True:
        token = scanner.get_next_token()

        if token.type == TokenType.EOF:
            break

        valores.append(token.value)

    assert valores == [
        "var",
        "x",
        "inteiro",
        ";",
        "x",
        "=",
        "10",
        ";"
    ]

def test_posicao_linha_coluna():
    codigo = "var x;\ninteiro y;"
    scanner = Scanner(codigo)

    token = scanner.get_next_token()
    assert token.value == "var"
    assert token.line == 1
    assert token.column == 1

    token = scanner.get_next_token()
    assert token.value == "x"
    assert token.line == 1
    assert token.column == 5

    token = scanner.get_next_token()
    assert token.value == ";"
    assert token.line == 1
    assert token.column == 6

    token = scanner.get_next_token()
    assert token.value == "inteiro"
    assert token.line == 2
    assert token.column == 1

    token = scanner.get_next_token()
    assert token.value == "y"
    assert token.line == 2
    assert token.column == 9

    token = scanner.get_next_token()
    assert token.value == ";"
    assert token.line == 2
    assert token.column == 10

def test_posicao_apos_comentario():
    codigo = "# comentário\nvar x;"
    scanner = Scanner(codigo)
    token = scanner.get_next_token()

    assert token.value == "var"
    assert token.line == 2
    assert token.column == 1

def test_erro_caractere_invalido():
    scanner = Scanner("@")
    token = scanner.get_next_token()

    assert token.type == TokenType.ERROR
    assert token.value == "@"

def test_erro_caractere_invalido_dolar():
    scanner = Scanner("$")
    token = scanner.get_next_token()

    assert token.type == TokenType.ERROR
    assert token.value == "$"

def test_erro_caractere_invalido_e_comercial():
    scanner = Scanner("&")
    token = scanner.get_next_token()

    assert token.type == TokenType.ERROR
    assert token.value == "&"

def test_erro_exclamacao_isolada():
    scanner = Scanner("!")
    token = scanner.get_next_token()

    assert token.type == TokenType.ERROR
    assert token.value == "!"

def test_erro_lexico_com_posicao():
    codigo = "var x;\n\n@"
    scanner = Scanner(codigo)
    scanner.get_next_token()  # var
    scanner.get_next_token()  # x
    scanner.get_next_token()  # ;    
    token = scanner.get_next_token()

    assert token.type == TokenType.ERROR
    assert token.value == "@"
    assert token.line == 3
    assert token.column == 1

def test_eof():
    scanner = Scanner("")
    token = scanner.get_next_token()

    assert token.type == TokenType.EOF
    assert token.value == ""

def test_eof_apos_tokens():
    scanner = Scanner("var x")
    scanner.get_next_token()
    scanner.get_next_token()
    token = scanner.get_next_token()

    assert token.type == TokenType.EOF

def test_programa_minilang_valido():
    codigo = """
    programa teste {
        var x inteiro;
        var ativo booleano;

        x = 10;
        ativo = verdadeiro;

        se (x >= 10 e ativo) {
            escreva x;
        }
    }
    fim.
    """

    scanner = Scanner(codigo)
    tokens = []

    while True:
        token = scanner.get_next_token()
        tokens.append(token)

        if token.type == TokenType.EOF:
            break

    # O teste verifica que o programa inteiro consegue ser tokenizado sem gerar erros léxicos.
    assert not any(
        token.type == TokenType.ERROR
        for token in tokens
    )
    assert tokens[-1].type == TokenType.EOF

def test_todas_categorias_de_tokens():
    codigo = """
    programa teste {
        var x inteiro;
        var y booleano;

        x = 10 + 20 * 2;
        y = verdadeiro e não falso;

        se (x >= 10 ou x != 0) {
            escreva x;
        }
    }
    fim.
    """

    scanner = Scanner(codigo)
    tipos = set()

    while True:
        token = scanner.get_next_token()
        tipos.add(token.type)

        if token.type == TokenType.EOF:
            break

    assert TokenType.KEYWORD in tipos
    assert TokenType.ID in tipos
    assert TokenType.INT in tipos
    assert TokenType.OP_ARIT in tipos
    assert TokenType.OP_REL in tipos
    assert TokenType.OP_LOGICO in tipos
    assert TokenType.ASSIGN in tipos
    assert TokenType.DELIM in tipos
    assert TokenType.EOF in tipos
