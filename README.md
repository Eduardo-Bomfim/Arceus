# Arceus — Compilador MiniLang ⚡

**Arceus** é um compilador/interpretador desenvolvido em **Python** gerenciado com **[uv](https://github.com/astral-sh/uv)** para a linguagem imperativa **MiniLang**, criado como produto avaliativo da disciplina de **Teoria da Computação e Compiladores** (UNIFACS 2026.2).

O projeto implementa o pipeline clássico de compilação, traduzindo conceitos de sistemas formais, autômatos e gramáticas livres de contexto em software executável.

---

## 🚀 Pipeline & Funcionalidades

- **Analisador Léxico (M1):** Reconhecimento manual de tokens via Autômato Finito Determinístico (AFD), descarte de espaços/comentários (`#`), tratamento de *lookahead* (`=`, `==`, `<`, `<=`, `>`, `>=`, `!=`) e rastreamento de linha/coluna.
- **Analisador Sintático & AST (M2):** Parser descendente recursivo LL(1) manual para a GLC da MiniLang, construção de Árvore Sintática Abstrata (AST) navegável com padrão *Visitor* (`PrintAstVisitor`), recuperação de erros em modo pânico (`synchronize()`) e resolução do *dangling else* por casamento guloso.
- **Analisador Semântico (M3):** Tabela de símbolos com pilha de escopos léxicos aninhados (`SymbolTable`), checagem e inferência de tipos (`inteiro`, `booleano`, sentinela `ERROR`), anotação de `inferred_type` na AST e análise de inicialização com fluxo condicional (`then` ∩ `else`).
- **Back-End, Otimização & Runtime (M4):** Interpretação direta da AST via padrão *Visitor* (`Interpreter`), runtime I/O interativo (`leia` / `escreva`), proteção contra loops infinitos (`--max-steps`) e pass de otimização por *Constant Folding* (`ConstantFolder`) com visualização antes/depois da árvore (`--opt --dump-ast`).
- **Extensão Obrigatória (Opção D):** Suporte léxico, sintático, semântico e de execução aos comandos de repetição `para` e `repita`/`ate` (`ForNode` / `RepeatNode`).

---

## 🛠️ Tecnologias & Ferramentas

- **Linguagem:** Python 3.13.12
- **Gerenciador de Pacotes e Ambiente:** [uv](https://github.com/astral-sh/uv)
- **Abordagem:** Implementação manual pura em Python (`@dataclass` + `Enum` + padrão *Visitor*, sem geradores externos)
- **Testes:** [pytest](https://docs.pytest.org/)

---

## 📋 Como Executar

O projeto utiliza o **`uv`** para gerenciar o ambiente virtual e dependências de forma rápida e reprodutível.

### 1. Pré-requisito

Certifique-se de ter o `uv` instalado:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clonar e Sincronizar o Ambiente

```bash
git clone -b develop https://github.com/Eduardo-Bomfim/Arceus.git
cd Arceus
uv sync
```

### 3. Executar o Compilador

```bash
# Executar um programa MiniLang (pipeline completo: Léxico -> Sintático -> Semântico -> Backend)
uv run python main.py caminho/do/programa.ml

# Executar com otimização por Constant Folding
uv run python main.py caminho/do/programa.ml --opt

# Comparar a AST antes e depois do Constant Folding (demonstração da otimização)
uv run python main.py caminho/do/programa.ml --opt --dump-ast

# Inspecionar a Árvore Sintática Abstrata (AST) anotada com tipos inferidos
uv run python main.py caminho/do/programa.ml --ast

# Exibir a tabela de símbolos (identificador, tipo, escopo, linha, coluna, inicialização)
uv run python main.py caminho/do/programa.ml --symbols

# Executar com proteção de limite de passos
uv run python main.py caminho/do/programa.ml --max-steps 10000

# Exibir tokens gerados pelo analisador léxico
uv run python main.py caminho/do/programa.ml --tokens
```

### 4. Rodar a Suíte de Testes

```bash
uv run pytest -v
```

---

## 📂 Estrutura do Projeto

```text
Arceus/
├── main.py                      # Ponto de entrada / CLI do compilador e interpretador
├── pyproject.toml               # Dependências e configuração do projeto (uv + pytest)
├── src/
│   ├── enum/
│   │   ├── token_type.py        # [M1] Categorias léxicas (TokenType)
│   │   └── data_type.py         # [M2/M3] Tipos da linguagem (DataType)
│   └── classes/
│       ├── token.py             # [M1] Dataclass Token
│       ├── scanner.py           # [M1] Scanner AFD manual com lookahead
│       ├── ast_nodes.py         # [M2] Nós da AST (@dataclass) e AstVisitor
│       ├── parser.py            # [M2] Parser LL(1) manual + modo pânico
│       ├── symbol_table.py      # [M3] Symbol e SymbolTable com pilha de escopos
│       ├── semantic.py          # [M3] SemanticAnalyzer(AstVisitor)
│       ├── optimizer.py         # [M4] ConstantFolder(AstVisitor) — pass de otimização
│       ├── interpreter.py       # [M4] Interpreter(AstVisitor) — backend e runtime I/O
│       └── visitors/
│           └── printer.py       # [M2] PrintAstVisitor (Pretty Printer)
└── test/
    ├── test_scanner.py          # [M1] Suíte unitária do léxico
    ├── test_parser.py           # [M2] Suíte do parser, AST, precedência e modo pânico
    ├── test_semantic.py         # [M3] Suíte de escopos, tipos, anotação e inicialização
    ├── test_interpreter.py       # [M4] Suíte de execução, I/O, otimização e runtime
    └── fixtures/
        ├── valid/               # Programas .ml válidos para regressão
        └── invalid/             # Programas .ml inválidos com erros esperados
```

---

## 👥 Equipe

- **Arthur Andrade Silva**
- **Eduardo de Andrade do Bomfim Júnior**
- **Valentin Eduardo Carvalho Bispo dos Santos**
- **Orientador:** Prof. Daniel Da Silva Lemos Santana — Universidade Salvador (UNIFACS)

- 
