"""Mapper dos dados de usuários para o contrato de entrega ao BFF."""

from typing import Any

_VISOES = ("codae", "dre", "ue", "empresa")


def mapear_usuarios(
    acesso_ativo: dict[str, int],
    por_tipo_perfil: dict[str, int],
) -> dict[str, Any]:
    """Monta o bloco ``usuarios`` do contrato."""
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
