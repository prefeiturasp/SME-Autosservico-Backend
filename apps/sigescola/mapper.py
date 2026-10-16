"""Mapper dos dados do SIG-Escola para o contrato de entrega ao BFF."""

from typing import Any

# paa_paa.status -> bucket do card. NAO_INICIADO fica fora.
_PAA_BUCKETS = {
    "EM_ELABORACAO": "em_andamento",
    "GERADO": "finalizados",
    "EM_RETIFICACAO": "em_retificacao",
}

# "Enviadas ou em andamento com as DREs" (discovery): todas as prestações
# menos NAO_RECEBIDA. NAO_APRESENTADA não existia no dump do discovery e
# fica fora junto. Decisão do PO pendente sobre NAO_RECEBIDA (ver plano).
_PC_NAO_ENVIADAS = frozenset({"NAO_RECEBIDA", "NAO_APRESENTADA"})


_DIAS_MEDIA = 30


def _hoje_sobre_a_media(hoje: int, total_30_dias: int) -> dict[str, Any]:
    """Valor de hoje e a variação (%) sobre a média diária de 30 dias."""
    media = total_30_dias / _DIAS_MEDIA
    variacao = round((hoje - media) / media * 100, 1) if media else 0.0
    return {"valor": hoje, "variacao_percentual_30_dias": variacao}


def mapear_usuarios(
    com_acesso: int, novos_30_dias: int, logins: dict[str, int]
) -> dict[str, Any]:
    """Monta o bloco ``usuarios`` do contrato.

    ``unicos_por_dia`` e ``acessos_hoje`` comparam hoje com a média diária
    dos 30 dias anteriores, em percentual.
    """
    return {
        "com_acesso_ativo": {
            "valor": com_acesso,
            "variacao_30_dias": novos_30_dias,
        },
        "unicos_por_dia": _hoje_sobre_a_media(
            logins["unicos_hoje"], logins["usuarios_dia_30_dias"]
        ),
        "acessos_hoje": _hoje_sobre_a_media(
            logins["acessos_hoje"], logins["acessos_30_dias"]
        ),
    }


def mapear_plano_anual(por_situacao: dict[str, int]) -> dict[str, int]:
    """Monta o bloco ``plano_anual_de_atividades`` por status do PAA."""
    return {
        nome: por_situacao.get(status, 0)
        for status, nome in _PAA_BUCKETS.items()
    }


def mapear_prestacao_de_contas(
    *,
    ues_aptas: int,
    por_situacao: dict[str, int],
    creditos: float,
    despesas: float,
    demonstrativos: int,
    devolucao: float,
) -> dict[str, Any]:
    """Monta o bloco ``prestacao_de_contas`` do contrato."""
    enviadas = sum(
        quantidade
        for status, quantidade in por_situacao.items()
        if status not in _PC_NAO_ENVIADAS
    )
    return {
        "ues_aptas": ues_aptas,
        "enviadas_ou_em_andamento": enviadas,
        "creditos_disponiveis": round(creditos, 2),
        "despesas_registradas": round(despesas, 2),
        "demonstrativos_gerados": demonstrativos,
        "devolucao_ao_tesouro": round(devolucao, 2),
    }


def mapear_situacao_patrimonial(
    quantidade: int, valor: float
) -> dict[str, Any]:
    """Monta o bloco ``situacao_patrimonial`` do contrato."""
    return {
        "quantidade_bens_produzidos": quantidade,
        "valor_bens_produzidos": round(valor, 2),
    }


def mapear_unidades(
    unidades: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Monta as opções de UE: código EOL e rótulo ``TIPO NOME``."""
    return [
        {
            "codigo_eol": unidade["codigo_eol"],
            "nome": " ".join(
                parte
                for parte in (unidade["tipo_unidade"], unidade["nome"])
                if parte
            ),
        }
        for unidade in unidades
    ]
