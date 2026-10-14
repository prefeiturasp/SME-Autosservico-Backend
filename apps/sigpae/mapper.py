"""Mapper dos dados do SIGPAE para o contrato de entrega ao BFF."""

from typing import Any

_VISOES = ("codae", "dre", "ue", "empresa")

# Categoria do painel -> status do workflow de SolicitacaoMedicaoInicial
# (SME-SIGPAE-API, src/medicao_inicial). "Correção solicitada" (DRE devolve
# à UE) entra em "aguardando_envio_ue", pois a UE precisa reenviar.
_MEDICOES_STATUS: dict[str, tuple[str, ...]] = {
    "aguardando_envio_ue": (
        "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
        "MEDICAO_CORRECAO_SOLICITADA",
    ),
    "enviadas_pelas_unidades": (
        "MEDICAO_ENVIADA_PELA_UE",
        "MEDICAO_CORRIGIDA_PELA_UE",
    ),
    "aprovadas_pelas_dres": ("MEDICAO_APROVADA_PELA_DRE",),
    "aguardando_codae": (
        "MEDICAO_CORRECAO_SOLICITADA_CODAE",
        "MEDICAO_CORRIGIDA_PARA_CODAE",
    ),
    "aprovadas_codae": ("MEDICAO_APROVADA_PELA_CODAE",),
}


# Prefixo do rótulo de cada balde do comparativo, por período.
_COMPARATIVO_ROTULOS = {
    "dia": "Dia",
    "quinzena": "Quinzena",
    "mes": "Semana",
    "trimestre": "Mês",
}


def mapear_comparativo_acessos(
    por_periodo: dict[str, list[int]],
) -> dict[str, Any]:
    """Monta os baldes do comparativo (rótulo + valor + pico) por período."""
    resultado: dict[str, Any] = {}
    for periodo, valores in por_periodo.items():
        prefixo = _COMPARATIVO_ROTULOS[periodo]
        pico = max(valores) if valores else 0
        indice_pico = valores.index(pico) if pico > 0 else -1
        resultado[periodo] = {
            "buckets": [
                {
                    "label": f"{prefixo} {indice + 1}",
                    "value": valor,
                    "isPeak": indice == indice_pico,
                }
                for indice, valor in enumerate(valores)
            ]
        }
    return resultado


def mapear_usuarios(
    acesso_ativo: dict[str, int],
    acessos: dict[str, int],
    por_tipo_perfil: dict[str, int],
    comparativo_acessos: dict[str, Any],
) -> dict[str, Any]:
    """Monta o bloco ``usuarios`` do contrato."""
    return {
        "com_acesso_ativo": {
            "total": acesso_ativo["total"],
            "ativos_30_dias": acesso_ativo["ativos_30_dias"],
            "novos_30_dias": acesso_ativo["novos_30_dias"],
        },
        "unicos_por_dia": acessos["unicos_por_dia"],
        "acessos_hoje": acessos["acessos_hoje"],
        "por_tipo_perfil": {
            visao: por_tipo_perfil.get(visao.upper(), 0) for visao in _VISOES
        },
        "comparativo_acessos": comparativo_acessos,
    }


def mapear_medicoes_iniciais(
    por_status: dict[str, int],
) -> dict[str, int]:
    """Monta o bloco ``medicoes_iniciais`` a partir dos status do funil."""
    return {
        categoria: sum(por_status.get(status, 0) for status in status_workflow)
        for categoria, status_workflow in _MEDICOES_STATUS.items()
    }


def mapear_produtos_homologados(dados: dict[str, int]) -> dict[str, int]:
    """Monta o bloco ``produtos_homologados`` do contrato."""
    return {
        "total_cadastrados": dados["total_cadastrados"],
        "homologados": dados["homologados"],
        "solicitacoes_no_mes": dados["solicitacoes_no_mes"],
        "solicitacoes_no_ano": dados["solicitacoes_no_ano"],
    }


def mapear_empresas_terceirizadas(dados: dict[str, int]) -> dict[str, int]:
    """Monta o bloco ``empresas_terceirizadas`` do contrato."""
    return {
        "cadastradas": dados["cadastradas"],
        "ativas": dados["ativas"],
    }


def mapear_solicitacoes(
    por_periodo: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    """Monta um bloco de solicitações por período (dia/quinzena/mês/tri)."""
    return {
        periodo: {
            "total": contagens["total"],
            "autorizadas": contagens["autorizadas"],
            "aguardando": contagens["aguardando"],
            "negadas": contagens["negadas"],
            "canceladas": contagens["canceladas"],
        }
        for periodo, contagens in por_periodo.items()
    }
