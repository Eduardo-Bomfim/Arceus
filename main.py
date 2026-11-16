from __future__ import annotations
import argparse
import sys
from pathlib import Path
from src.classes.parser import Parser
from src.classes.scanner import Scanner
from src.classes.visitors.printer import PrintAstVisitor
from src.enum.token_type import TokenType

def build_arg_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(
        prog="arceus",
        description="Compilador MiniLang (Arceus) — Análise Léxica e Sintática com AST",
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
    ast = parser.parse()

    has_errors = parser.had_lexical_error or bool(parser.errors)

    if args.dump_ast and ast is not None and not has_errors:
        printer = PrintAstVisitor()
        print(ast.accept(printer))

    if has_errors:
        return 1

    if not args.dump_ast:
        print("Análise léxica e sintática concluída sem erros.")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
