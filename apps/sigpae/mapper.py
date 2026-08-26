"""Mapper dos dados do SIGPAE para o contrato de entrega ao BFF."""

from typing import Any

_VISOES = ("codae", "dre", "ue", "empresa")

_MEDICOES_CATEGORIAS = (
    "aguardando_envio_ue",
    "enviadas_pelas_unidades",
    "aprovadas_pelas_dres",
    "aguardando_codae",
    "aprovadas_codae",
)


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


def mapear_medicoes_iniciais() -> dict[str, Any]:
    """Monta o bloco ``medicoes_iniciais`` do contrato."""
    return dict.fromkeys(_MEDICOES_CATEGORIAS)
