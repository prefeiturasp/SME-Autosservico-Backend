"""Parser dos dados de usuários vindos do banco do SIGPAE."""

from typing import Any


def parse_acesso_ativo(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única da query de acesso ativo."""
    linha = linhas[0] if linhas else {}
    return {
        "total": int(linha.get("total") or 0),
        "ativos_30_dias": int(linha.get("ativos_30_dias") or 0),
    }


def parse_por_tipo_perfil(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta as linhas de usuários por tipo de perfil."""
    return {
        str(linha["visao"]).upper(): int(linha["total_usuarios"] or 0)
        for linha in linhas
        if linha.get("visao")
    }
