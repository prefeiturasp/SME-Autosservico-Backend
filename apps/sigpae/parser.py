"""Parser dos dados de usuários vindos do banco do SIGPAE.

Interpreta as linhas cruas retornadas pelas queries, sem aplicar regra
de contrato (isso é responsabilidade do mapper).
"""

from typing import Any


def parse_acesso_ativo(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única da query de acesso ativo.

    Args:
        linhas: Linhas retornadas por ``USUARIOS_ACESSO_ATIVO``.

    Returns:
        Dicionário com ``total`` e ``ativos_30_dias`` (zero quando a
        consulta não retorna linhas).
    """
    linha = linhas[0] if linhas else {}
    return {
        "total": int(linha.get("total") or 0),
        "ativos_30_dias": int(linha.get("ativos_30_dias") or 0),
    }


def parse_por_tipo_perfil(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta as linhas de usuários por tipo de perfil.

    Args:
        linhas: Linhas retornadas por ``USUARIOS_POR_TIPO_PERFIL``.

    Returns:
        Dicionário ``visao``→``total_usuarios`` com a visão em maiúsculas.
    """
    return {
        str(linha["visao"]).upper(): int(linha["total_usuarios"] or 0)
        for linha in linhas
        if linha.get("visao")
    }
