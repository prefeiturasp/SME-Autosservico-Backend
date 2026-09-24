"""Parser dos dados vindos do banco do SGP."""

from typing import Any


def parse_acesso_ativo(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de usuários com acesso ativo."""
    linha = linhas[0] if linhas else {}
    return {
        "valor": int(linha.get("total") or 0),
        "variacao_30_dias": int(linha.get("ativos_30_dias") or 0),
    }


def parse_de_unidades(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de usuários de unidades educacionais."""
    linha = linhas[0] if linhas else {}
    return {
        "total": int(linha.get("total") or 0),
        "diretorias_regionais": int(linha.get("diretorias") or 0),
    }


def parse_por_situacao(linhas: list[dict[str, Any]]) -> dict[int, int]:
    """Interpreta linhas ``(situacao, quantidade)`` num dicionário."""
    return {
        int(linha["situacao"]): int(linha["quantidade"] or 0)
        for linha in linhas
        if linha.get("situacao") is not None
    }


def parse_escalar(linhas: list[dict[str, Any]], campo: str) -> int:
    """Extrai um único inteiro da primeira linha do resultado."""
    linha = linhas[0] if linhas else {}
    return int(linha.get(campo) or 0)
