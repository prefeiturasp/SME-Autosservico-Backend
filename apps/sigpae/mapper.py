"""Mapper dos dados de usuários para o contrato de entrega ao BFF.

Transforma a saída do parser no bloco ``usuarios`` do contrato. Os
indicadores sem fonte de dado no SIGPAE (únicos por dia, acessos hoje,
comparativo de acessos) são entregues como ``None`` — gap aceito como
decisão de produto no Discovery (AB#154283).
"""

from typing import Any

_VISOES = ("codae", "dre", "ue", "empresa")


def mapear_usuarios(
    acesso_ativo: dict[str, int],
    por_tipo_perfil: dict[str, int],
) -> dict[str, Any]:
    """Monta o bloco ``usuarios`` do contrato.

    Args:
        acesso_ativo: Saída de ``parser.parse_acesso_ativo``.
        por_tipo_perfil: Saída de ``parser.parse_por_tipo_perfil``.

    Returns:
        Bloco ``usuarios`` no formato do contrato de entrega.
    """
    return {
        "com_acesso_ativo": {
            "total": acesso_ativo["total"],
            "ativos_30_dias": acesso_ativo["ativos_30_dias"],
        },
        "unicos_por_dia": None,
        "acessos_hoje": None,
        "por_tipo_perfil": {
            visao: por_tipo_perfil.get(visao.upper(), 0) for visao in _VISOES
        },
        "comparativo_acessos": None,
    }
