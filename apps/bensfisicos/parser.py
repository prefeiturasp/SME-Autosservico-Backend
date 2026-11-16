"""Parser dos dados vindos do banco do Bens Físicos."""

from typing import Any


def _primeira(linhas: list[dict[str, Any]]) -> dict[str, Any]:
    """Primeira linha do resultado, ou vazia."""
    return linhas[0] if linhas else {}


def parse_inteiros(
    linhas: list[dict[str, Any]], campos: tuple[str, ...]
) -> dict[str, int]:
    """Lê contadores da linha única do resultado (``NULL`` = 0)."""
    linha = _primeira(linhas)
    return {campo: int(linha.get(campo) or 0) for campo in campos}


def parse_decimal(linhas: list[dict[str, Any]], campo: str) -> float:
    """Lê um valor decimal da linha única (``NULL`` = 0)."""
    return float(_primeira(linhas).get(campo) or 0)


def parse_por_unidade(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpreta linhas ``(sigla, nome, bens)`` por unidade administrativa."""
    return [
        {
            "sigla": linha.get("sigla"),
            "nome": str(linha["nome"]),
            "bens": int(linha["bens"] or 0),
        }
        for linha in linhas
    ]
