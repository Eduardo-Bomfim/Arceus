from __future__ import annotations
from dataclasses import dataclass
from src.enum.data_type import DataType

@dataclass
class Symbol:
    """Representa uma variável declarada na tabela de símbolos."""

    name: str
    data_type: DataType
    line: int
    column: int
    initialized: bool = False
    scope_level: int = 0

class SymbolTable:
    """Tabela de símbolos com pilha de escopos léxicos aninhados."""

    def __init__(self) -> None:
        self.scopes: list[dict[str, Symbol]] = []
        self.all_symbols: list[Symbol] = []

    @property
    def current_scope_level(self) -> int:
        return len(self.scopes) - 1

    def enter_scope(self) -> None:
        """Abre um novo escopo léxico no topo da pilha."""
        self.scopes.append({})

    def exit_scope(self) -> dict[str, Symbol]:
        """Fecha o escopo léxico atual, removendo-o do topo da pilha."""
        if not self.scopes:
            raise RuntimeError("Não há escopo ativo para encerrar.")
        return self.scopes.pop()

    def declare(self, symbol: Symbol) -> bool:
        """Registra um símbolo no escopo atual.

        Retorna False se já existir declaração com o mesmo nome neste escopo.
        """
        if not self.scopes:
            raise RuntimeError("Nenhum escopo ativo para declarar símbolo.")

        if self.lookup_local(symbol.name) is not None:
            return False

        symbol.scope_level = self.current_scope_level
        self.scopes[-1][symbol.name] = symbol
        self.all_symbols.append(symbol)
        return True

    def lookup_local(self, name: str) -> Symbol | None:
        """Busca um símbolo exclusivamente no escopo atual (detecta redeclaração)."""
        if not self.scopes:
            return None
        return self.scopes[-1].get(name)

    def lookup(self, name: str) -> Symbol | None:
        """Busca encadeada do escopo mais interno até o escopo mais externo."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def snapshot_initialization(self) -> dict[int, bool]:
        """Captura o estado de inicialização de todos os símbolos atualmente visíveis."""
        return {
            id(symbol): symbol.initialized
            for scope in self.scopes
            for symbol in scope.values()
        }

    def restore_initialization(self, snapshot: dict[int, bool]) -> None:
        """Restaura o estado de inicialização dos símbolos presentes no snapshot."""
        for scope in self.scopes:
            for symbol in scope.values():
                if id(symbol) in snapshot:
                    symbol.initialized = snapshot[id(symbol)]

    def intersect_initialization(
        self,
        before: dict[int, bool],
        branch_a: dict[int, bool],
        branch_b: dict[int, bool],
    ) -> None:
        """Mantém inicializado apenas o que foi garantidamente inicializado em ambos os ramos."""
        for scope in self.scopes:
            for symbol in scope.values():
                sym_id = id(symbol)
                if sym_id in before:
                    symbol.initialized = (
                        branch_a.get(sym_id, False) and branch_b.get(sym_id, False)
                    )

    def format_table(self) -> str:
        """Formata o histórico de símbolos declarados para inspeção em CLI/depuração."""
        header = "Nome | Tipo | Escopo | Linha | Coluna | Inicializada"
        separator = "-" * len(header)
        rows = [header, separator]
        for sym in self.all_symbols:
            init_str = "sim" if sym.initialized else "não"
            rows.append(
                f"{sym.name} | {sym.data_type.name} | {sym.scope_level} | "
                f"{sym.line} | {sym.column} | {init_str}"
            )
        return "\n".join(rows)
