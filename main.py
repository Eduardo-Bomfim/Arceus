from __future__ import annotations
import argparse
import sys
from pathlib import Path
from src.classes.parser import Parser
from src.classes.scanner import Scanner
from src.classes.semantic import SemanticAnalyzer
from src.classes.visitors.printer import PrintAstVisitor
from src.enum.token_type import TokenType

def build_arg_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(
        prog="arceus",
        description="Compilador MiniLang (Arceus) — Análise Léxica, Sintática e Semântica",
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
        help="Imprime a Árvore Sintática Abstrata (AST) anotada com tipos inferidos",
    )
    arg_parser.add_argument(
        "--symbols",
        action="store_true",
        help="Exibe a tabela de símbolos gerada pela análise semântica",
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

    if parser.had_lexical_error or parser.errors or ast is None:
        return 1

    analyzer = SemanticAnalyzer()
    semantic_ok = analyzer.analyze(ast)

    if not semantic_ok:
        return 1

    if args.dump_ast:
        printer = PrintAstVisitor()
        print(ast.accept(printer))

    if args.symbols:
        print(analyzer.symbol_table.format_table())

    if not args.dump_ast and not args.symbols:
        print("Análise léxica, sintática e semântica concluída sem erros.")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
