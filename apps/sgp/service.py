"""Serviço de métricas do SGP."""

import logging
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.sgp import handler
from apps.sgp.periodo import Periodo

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600
CACHE_TTL_PERIODOS_SEGUNDOS = 6 * 3600
CHAVE_CACHE_PERIODOS = "sgp:periodos"


def _chave_cache(periodo: Periodo) -> str:
    """Chave de cache do contrato, por ano, segmento, semestre e bimestre."""
    return (
        f"sgp:metricas:{periodo.ano_letivo}:{periodo.segmento}:"
        f"{periodo.semestre or 0}:{periodo.bimestre}"
    )


def _contrato(
    periodo: Periodo,
    *,
    atualizado_em: str | None,
    usuarios: dict[str, Any] | None,
    frequencias: dict[str, Any] | None,
    sondagens: dict[str, Any] | None,
    fechamento: dict[str, Any] | None,
    conselho_classe: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do SGP."""
    return {
        "atualizado_em": atualizado_em,
        "ano_letivo": periodo.ano_letivo,
        "bimestre": periodo.bimestre,
        "periodo": periodo.como_contrato(),
        "usuarios": usuarios,
        "frequencias": frequencias,
        "sondagens": sondagens,
        "fechamento": fechamento,
        "conselho_classe": conselho_classe,
    }


def _indisponivel(periodo: Periodo) -> dict[str, Any]:
    """Contrato degradado: todos os blocos nulos."""
    return _contrato(
        periodo,
        atualizado_em=None,
        usuarios=None,
        frequencias=None,
        sondagens=None,
        fechamento=None,
        conselho_classe=None,
    )


def obter_metricas(periodo: Periodo) -> dict[str, Any]:
    """Retorna o contrato de métricas do SGP para o período.

    Só fechamento e conselho filtram por segmento e semestre.
    """
    chave = _chave_cache(periodo)
    cacheado: dict[str, Any] | None = cache.get(chave)
    if cacheado is not None:
        return cacheado

    ano_letivo, bimestre = periodo.ano_letivo, periodo.bimestre
    try:
        contrato = _contrato(
            periodo,
            atualizado_em=timezone.now().isoformat(),
            usuarios=handler.obter_usuarios(),
            frequencias=handler.obter_frequencias(ano_letivo, bimestre),
            sondagens=handler.obter_sondagens(ano_letivo, bimestre),
            fechamento=handler.obter_fechamento(periodo),
            conselho_classe=handler.obter_conselho_classe(periodo),
        )
    except psycopg.Error:
        logger.exception("Falha ao coletar métricas do SGP")
        return _indisponivel(periodo)

    cache.set(chave, contrato, CACHE_TTL_SEGUNDOS)
    return contrato


def obter_periodos() -> dict[str, Any]:
    """Opções do filtro de período, do ano corrente e do anterior.

    Se o banco falhar, devolve ``periodos`` nulo e não cacheia.
    """
    cacheado: dict[str, Any] | None = cache.get(CHAVE_CACHE_PERIODOS)
    if cacheado is not None:
        return cacheado

    ano_corrente = timezone.localdate().year
    try:
        contrato = {
            "periodos": handler.obter_periodos(ano_corrente - 1, ano_corrente)
        }
    except psycopg.Error:
        logger.exception("Falha ao coletar períodos do SGP")
        return {"periodos": None}

    cache.set(CHAVE_CACHE_PERIODOS, contrato, CACHE_TTL_PERIODOS_SEGUNDOS)
    return contrato
