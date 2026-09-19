# Arceus — Compilador MiniLang ⚡

**Arceus** é um compilador/interpretador completo desenvolvido em **Python** gerenciado com **[uv](https://github.com/astral-sh/uv)** para a linguagem imperativa **MiniLang**, criado como produto avaliativo da disciplina de **Teoria da Computação e Compiladores** (UNIFACS 2026.2).

O projeto implementa o pipeline clássico de compilação, traduzindo conceitos de sistemas formais, autômatos e gramáticas livres de contexto em software executável.

---

## 🚀 Pipeline & Funcionalidades

- **Analisador Léxico (M1):** Reconhecimento de tokens via AFD/expressões regulares, descarte de espaços/comentários (`#`), tratamento de *lookahead* (`==`, `<=`, etc.) e rastreamento de linha/coluna.
- **Analisador Sintático & AST (M2):** Parser para a GLC da MiniLang, construção de Árvore Sintática Abstrata (AST), recuperação de erros (modo pânico) e tratamento do *dangling else*.
- **Analisador Semântico (M3):** Tabela de símbolos com suporte a escopos, checagem/inferência de tipos (`inteiro`, `booleano`), anotação da AST e detecção de variáveis não declaradas ou inconsistências.
- **Back-End & Otimização (M4):** Geração de código intermediário de 3 endereços (3AC) ou interpretação direta da AST, com demonstração de otimização de código.
- **Extensão:** Implementação de funcionalidade estendida obrigatória conforme o edital.

---

## 🛠️ Tecnologias & Ferramentas

- **Linguagem:** Python 3.13.12
- **Gerenciador de Pacotes e Ambiente:** [uv](https://github.com/astral-sh/uv)
- **Ferramentas:** *(Ex.: implementação manual pura ou gerador como PLY)*

---

## 📋 Como Executar

O projeto utiliza o **`uv`** para gerenciar o ambiente virtual e dependências de forma rápida e reprodutível.

### 1. Pré-requisito

Certifique-se de ter o `uv` instalado:
```bash
# macOS/Linux
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

# Windows (PowerShell)
powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"