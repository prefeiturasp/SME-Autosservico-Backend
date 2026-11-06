"""Mapper dos dados do SGP para o contrato de entrega ao BFF."""

from typing import Any

from apps.sgp.periodo import SEGMENTO_EJA
from apps.sgp.periodo import SEGMENTO_FUNDAMENTAL_MEDIO

# Enum SituacaoFechamento (0 e 1 são unidos em "não iniciados" na query).
_FECHAMENTO_BUCKETS = {
    0: "nao_iniciados",
    2: "processado_pendencias",
    3: "processado_sucesso",
    4: "processado_erro",
}

# Enum SituacaoConselhoClasse: 1 = em andamento, 2 = concluído. O bucket
# "não iniciados" não é contagem direta — é calculado (ver mapear_conselho).
_CONSELHO_EM_ANDAMENTO = 1
_CONSELHO_CONCLUIDO = 2


def mapear_usuarios(
    acesso_ativo: dict[str, int],
    de_unidades: dict[str, int],
) -> dict[str, Any]:
    """Monta o bloco ``usuarios`` do contrato."""
    return {
        "com_acesso_ativo": {
            "valor": acesso_ativo["valor"],
            "variacao_30_dias": acesso_ativo["variacao_30_dias"],
        },
        "de_unidades_educacionais": {
            "total": de_unidades["total"],
            "diretorias_regionais": de_unidades["diretorias_regionais"],
        },
        "unicos_por_dia": None,
        "acessos_por_hora": None,
    }


def _somar_por_dre(por_dre: list[dict[str, Any]]) -> dict[str, int]:
    """Soma os campos numéricos das DREs no total geral."""
    total: dict[str, int] = {}
    for linha in por_dre:
        for campo, valor in linha.items():
            if campo != "dre":
                total[campo] = total.get(campo, 0) + valor
    return total


def mapear_fechamento(
    por_dre_situacao: dict[str, dict[int, int]],
) -> dict[str, Any]:
    """Monta o bloco ``fechamento``, com o total e a quebra por DRE.

    O SGP não guarda o total previsto, então ele é a soma das situações.
    """
    por_dre = []
    for dre in sorted(por_dre_situacao):
        situacoes = por_dre_situacao[dre]
        buckets = {
            nome: int(situacoes.get(codigo, 0))
            for codigo, nome in _FECHAMENTO_BUCKETS.items()
        }
        por_dre.append(
            {"dre": dre, "previsto": sum(buckets.values()), **buckets}
        )
    total = _somar_por_dre(por_dre)
    return {
        "esperado": total.get("previsto", 0),
        **{nome: total.get(nome, 0) for nome in _FECHAMENTO_BUCKETS.values()},
        "por_dre": por_dre,
    }


def mapear_conselho_classe(
    por_dre_situacao: dict[str, dict[int, int]],
    previsto_por_dre: dict[str, int],
) -> dict[str, Any]:
    """Monta o bloco ``conselho_classe``, com o total e a quebra por DRE.

    Não iniciados = previsto - (em andamento + concluído), sem ficar negativo.
    """
    por_dre = []
    for dre in sorted(set(por_dre_situacao) | set(previsto_por_dre)):
        situacoes = por_dre_situacao.get(dre, {})
        previsto = int(previsto_por_dre.get(dre, 0))
        em_andamento = int(situacoes.get(_CONSELHO_EM_ANDAMENTO, 0))
        concluido = int(situacoes.get(_CONSELHO_CONCLUIDO, 0))
        por_dre.append(
            {
                "dre": dre,
                "previsto": previsto,
                "nao_iniciados": max(previsto - (em_andamento + concluido), 0),
                "em_andamento": em_andamento,
                "processado_sucesso": concluido,
            }
        )
    total = _somar_por_dre(por_dre)
    return {
        "esperado": total.get("previsto", 0),
        "nao_iniciados": total.get("nao_iniciados", 0),
        "em_andamento": total.get("em_andamento", 0),
        "processado_sucesso": total.get("processado_sucesso", 0),
        "por_dre": por_dre,
    }


# tipo_calendario.modalidade -> segmento do filtro.
_SEGMENTO_POR_MODALIDADE_CALENDARIO = {
    1: SEGMENTO_FUNDAMENTAL_MEDIO,
    2: SEGMENTO_EJA,
}


def mapear_periodos(periodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Monta as opções do filtro de período (semestre só na EJA)."""
    return [
        {
            "ano_letivo": periodo["ano_letivo"],
            "segmento": segmento,
            "semestre": (
                periodo["semestre"] if segmento == SEGMENTO_EJA else None
            ),
            "bimestre": periodo["bimestre"],
            "inicio": periodo["inicio"].isoformat(),
            "fim": periodo["fim"].isoformat(),
        }
        for periodo in periodos
        if (
            segmento := _SEGMENTO_POR_MODALIDADE_CALENDARIO.get(
                periodo["modalidade"]
            )
        )
    ]


def mapear_frequencias(dados: dict[str, int]) -> dict[str, Any]:
    """Monta o bloco ``frequencias`` (lançadas/esperadas + percentual)."""
    lancadas = dados["lancadas"]
    esperadas = dados["esperadas"]
    percentual = round(lancadas / esperadas * 100, 1) if esperadas else 0.0
    return {
        "lancadas": lancadas,
        "esperadas": esperadas,
        "percentual": percentual,
    }


def mapear_sondagens(dados: dict[str, int]) -> dict[str, Any]:
    """Monta o bloco ``sondagens`` (realizadas/esperadas)."""
    return {
        "realizadas": dados["realizadas"],
        "esperadas": dados["esperadas"],
    }
