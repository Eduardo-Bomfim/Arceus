from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.classes.interpreter import Interpreter
from src.classes.optimizer import ConstantFolder
from src.classes.parser import Parser
from src.classes.scanner import Scanner
from src.classes.semantic import SemanticAnalyzer
from src.classes.visitors.printer import PrintAstVisitor
from src.enum.token_type import TokenType


def build_arg_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(
        prog="arceus",
        description="Compilador e Interpretador MiniLang (Arceus) — Léxico, Sintático, Semântico e Backend",
    )
    arg_parser.add_argument(
        "file",
        type=Path,
        help="Caminho para o arquivo fonte MiniLang (.ml)",
    )
    arg_parser.add_argument(
        "--tokens",
        action="store_true",
        help="Exibe a sequência de tokens gerada pelo analisador léxico",
    )
    arg_parser.add_argument(
        "--ast",
        "--dump-ast",
        dest="dump_ast",
        action="store_true",
        help="Imprime a Árvore Sintática Abstrata (AST) formatada",
    )
    arg_parser.add_argument(
        "--symbols",
        action="store_true",
        help="Exibe a tabela de símbolos gerada pela análise semântica",
    )
    arg_parser.add_argument(
        "--opt",
        action="store_true",
        help="Ativa o pass de otimização por Constant Folding",
    )
    arg_parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Limite máximo de passos/iterações na execução (proteção contra loops infinitos)",
    )
    return arg_parser


def main(argv: list[str] | None = None) -> int:
    arg_parser = build_arg_parser()
    args = arg_parser.parse_args(argv)

    source_path: Path = args.file
    if not source_path.is_file():
        print(
            f"[Erro] Arquivo não encontrado: '{source_path}'",
            file=sys.stderr,
        )
        return 1

    source_code = source_path.read_text(encoding="utf-8")

    if args.tokens:
        token_scanner = Scanner(source_code)
        while True:
            tok = token_scanner.get_next_token()
            print(tok)
            if tok.type == TokenType.EOF:
                break

    scanner = Scanner(source_code)
    parser = Parser(scanner)
    raw_ast = parser.parse()

    if parser.had_lexical_error or parser.errors or raw_ast is None:
        return 1

    analyzer = SemanticAnalyzer()
    semantic_ok = analyzer.analyze(raw_ast)

    if not semantic_ok:
        return 1

    printer = PrintAstVisitor()

    # Pass de otimização por Constant Folding
    target_ast = raw_ast
    if args.opt:
        optimizer = ConstantFolder()
        target_ast = optimizer.optimize(raw_ast)

    # Exibição da AST (antes e depois caso --opt seja utilizado)
    if args.dump_ast:
        if args.opt:
            print("=== AST Original ===")
            print(printer.format(raw_ast))
            print("=== AST Otimizada (Constant Folding) ===")
            print(printer.format(target_ast))
        else:
            print(printer.format(raw_ast))

    # Exibição da tabela de símbolos
    if args.symbols:
        print(analyzer.symbol_table.format_table())

    # Se apenas foi solicitada inspeção (--tokens, --dump-ast ou --symbols), encerra sem interpretar
    if args.tokens or args.dump_ast or args.symbols:
        return 0

    # Execução do programa via Interpretador
    interpreter = Interpreter(max_steps=args.max_steps)
    success = interpreter.interpret(target_ast)

    if not success:
        return 1

    print("Programa executado com sucesso sem erros.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
