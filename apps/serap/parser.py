"""Parser dos dados de provas vindos do banco do SERAp Estudantes."""

from typing import Any

_CAMPOS = ("total", "finalizadas", "nao_finalizadas", "iniciadas_hoje")


def parse_provas(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única do agregado de provas."""
    linha = linhas[0] if linhas else {}
    return {campo: int(linha.get(campo) or 0) for campo in _CAMPOS}


def parse_acesso_ativo(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de usuários com acesso ativo."""
    linha = linhas[0] if linhas else {}
    return {
        "valor": int(linha.get("total") or 0),
        "variacao_30_dias": int(linha.get("novos_30_dias") or 0),
    }
