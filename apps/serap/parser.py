"""Parser dos dados de provas vindos do banco do SERAp Estudantes."""

from typing import Any

_CAMPOS = ("total", "finalizadas", "nao_finalizadas", "iniciadas_hoje")


def parse_provas(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única do agregado de provas."""
    linha = linhas[0] if linhas else {}
    return {campo: int(linha.get(campo) or 0) for campo in _CAMPOS}
