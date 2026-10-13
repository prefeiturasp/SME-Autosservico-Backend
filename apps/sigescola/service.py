"""Serviço de métricas do SIG-Escola (PTRF)."""

import logging
import time
from datetime import date
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.sigescola import handler

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600


class PeriodoNaoEncontradoError(ValueError):
    """O período pedido não existe no PTRF."""


def _contem(periodo: dict[str, Any], dia: date) -> bool:
    """Indica se ``dia`` cai dentro da janela do período."""
    fim = periodo["data_fim"]
    return periodo["data_inicio"] <= dia and (fim is None or dia <= fim)


def resolver_janela(
    periodos: list[dict[str, Any]],
    periodo: str | None,
    data_inicio: date | None,
    data_fim: date | None,
    hoje: date,
) -> tuple[str | None, date, date]:
    """Converte os filtros de data em ``(referencia, inicio, fim)``.

    O intervalo de datas vale como veio, sem período. Sem nenhum filtro,
    vale o período corrente: o que contém ``hoje`` ou, se nenhum contiver,
    o mais recente. O período corrente ainda não tem fim e termina hoje.

    Raises:
        PeriodoNaoEncontradoError: ``periodo`` não existe no PTRF.
    """
    if data_inicio is not None and data_fim is not None:
        return None, data_inicio, data_fim
    if periodo is None:
        escolhido = next(
            (p for p in periodos if _contem(p, hoje)),
            periodos[0] if periodos else None,
        )
    else:
        escolhido = next(
            (p for p in periodos if p["referencia"] == periodo), None
        )
    if escolhido is None:
        raise PeriodoNaoEncontradoError(periodo)
    return (
        escolhido["referencia"],
        escolhido["data_inicio"],
        escolhido["data_fim"] or hoje,
    )


def _chave_cache(*filtros: object) -> str:
    """Chave de cache do contrato, pelos filtros recebidos."""
    return "sigescola:metricas:" + ":".join(str(f or "") for f in filtros)


def _filtros(
    periodo: str | None,
    inicio: date | None,
    fim: date | None,
    dre: str | None,
    ue: str | None,
) -> dict[str, str | None]:
    """Filtros aplicados, como vão no contrato."""
    return {
        "periodo": periodo,
        "data_inicio": inicio.isoformat() if inicio else None,
        "data_fim": fim.isoformat() if fim else None,
        "dre": dre,
        "ue": ue,
    }


def _contrato(
    filtros: dict[str, str | None],
    *,
    atualizado_em: str | None,
    opcoes: dict[str, Any] | None,
    usuarios: dict[str, Any] | None,
    plano_anual: dict[str, Any] | None,
    prestacao_de_contas: dict[str, Any] | None,
    situacao_patrimonial: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do SIG-Escola."""
    return {
        "atualizado_em": atualizado_em,
        "filtros": filtros,
        "opcoes": opcoes,
        "usuarios": usuarios,
        "plano_anual_de_atividades": plano_anual,
        "prestacao_de_contas": prestacao_de_contas,
        "situacao_patrimonial": situacao_patrimonial,
    }


def obter_metricas(
    periodo: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    dre: str | None = None,
    ue: str | None = None,
) -> dict[str, Any]:
    """Retorna o contrato de métricas do SIG-Escola para os filtros.

    Raises:
        PeriodoNaoEncontradoError: ``periodo`` não existe no PTRF.
    """
    chave = _chave_cache(periodo, data_inicio, data_fim, dre, ue)
    cacheado: dict[str, Any] | None = cache.get(chave)
    if cacheado is not None:
        return cacheado

    inicio_coleta = time.monotonic()
    try:
        periodos = handler.obter_periodos()
        referencia, inicio, fim = resolver_janela(
            periodos, periodo, data_inicio, data_fim, timezone.localdate()
        )
        filtro: handler.Filtro = {
            "inicio": inicio,
            "fim": fim,
            "dre": dre,
            "ue": ue,
        }
        contrato = _contrato(
            _filtros(referencia, inicio, fim, dre, ue),
            atualizado_em=timezone.now().isoformat(),
            opcoes={
                "periodos": [p["referencia"] for p in periodos],
                "unidades": handler.obter_unidades(dre) if dre else [],
            },
            usuarios=handler.obter_usuarios(),
            plano_anual=handler.obter_plano_anual(filtro),
            prestacao_de_contas=handler.obter_prestacao_de_contas(filtro),
            situacao_patrimonial=handler.obter_situacao_patrimonial(filtro),
        )
    except psycopg.Error:
        logger.exception("Falha ao coletar métricas do SIG-Escola")
        return _contrato(
            _filtros(periodo, data_inicio, data_fim, dre, ue),
            atualizado_em=None,
            opcoes=None,
            usuarios=None,
            plano_anual=None,
            prestacao_de_contas=None,
            situacao_patrimonial=None,
        )

    logger.info(
        "Métricas do SIG-Escola coletadas em %.0f ms "
        "(periodo=%s, inicio=%s, fim=%s, dre=%s, ue=%s)",
        (time.monotonic() - inicio_coleta) * 1000,
        referencia,
        inicio,
        fim,
        dre,
        ue,
    )
    cache.set(chave, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
