"""Parser dos dados vindos dos bancos do GIPE."""

from datetime import date
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


def parse_dias(
    linhas: list[dict[str, Any]], campos: tuple[str, ...]
) -> dict[str, float | None]:
    """Lê médias da linha única; ``NULL`` (sem ocorrência) vira ``None``."""
    linha = _primeira(linhas)
    return {
        campo: None if linha.get(campo) is None else float(linha[campo])
        for campo in campos
    }


def parse_contagem(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta linhas ``(codigo, total)``; código nulo vira ``""``."""
    contagem: dict[str, int] = {}
    for linha in linhas:
        codigo = str(linha.get("codigo") or "")
        contagem[codigo] = contagem.get(codigo, 0) + int(linha["total"] or 0)
    return contagem


def parse_contagem_com_nome(
    linhas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Interpreta linhas ``(codigo, nome, total)`` do banco de usuários."""
    return [
        {
            "codigo": str(linha.get("codigo") or ""),
            "nome": linha.get("nome"),
            "total": int(linha["total"] or 0),
        }
        for linha in linhas
    ]


def parse_nomes(linhas: list[dict[str, Any]], chave: str) -> dict[str, str]:
    """Interpreta linhas ``(chave, nome)`` num dicionário."""
    return {
        str(linha[chave]): str(linha["nome"])
        for linha in linhas
        if linha.get("nome")
    }


def parse_por_tipo(
    linhas: list[dict[str, Any]],
) -> dict[bool, dict[str, int]]:
    """Separa a contagem por tipo em patrimonial (``True``) e não."""
    por_categoria: dict[bool, dict[str, int]] = {True: {}, False: {}}
    for linha in linhas:
        tipos = por_categoria[bool(linha["patrimonial"])]
        nome = str(linha["nome"])
        tipos[nome] = tipos.get(nome, 0) + int(linha["total"] or 0)
    return por_categoria


def parse_por_mes(linhas: list[dict[str, Any]]) -> list[tuple[date, int]]:
    """Interpreta a série mensal ``(mes, total)``, em ordem."""
    return [(linha["mes"], int(linha["total"] or 0)) for linha in linhas]


def parse_por_bimestre(linhas: list[dict[str, Any]]) -> dict[int, int]:
    """Interpreta linhas ``(bimestre, total)``."""
    return {
        int(linha["bimestre"]): int(linha["total"] or 0) for linha in linhas
    }


def parse_analistas(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpreta as ocorrências tratadas por RF de analista."""
    return [
        {
            "username": str(linha["username"]),
            "ocorrencias_tratadas": int(linha["ocorrencias_tratadas"] or 0),
            "tempo_medio_dias": float(linha["tempo_medio_dias"] or 0),
        }
        for linha in linhas
    ]


def parse_perfis(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpreta a contagem de usuários por cargo x administrador."""
    return [
        {
            "cargo": str(linha["cargo"]),
            "admin": bool(linha["admin"]),
            "total": int(linha["total"] or 0),
        }
        for linha in linhas
    ]
