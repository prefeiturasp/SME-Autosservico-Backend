"""Serviço de métricas do SGP."""

import logging
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.sgp import handler

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600


def _chave_cache(ano_letivo: int, bimestre: int) -> str:
    """Chave de cache do contrato, por ano letivo e bimestre."""
    return f"sgp:metricas:{ano_letivo}:{bimestre}"


def _contrato(
    ano_letivo: int,
    bimestre: int,
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
        "ano_letivo": ano_letivo,
        "bimestre": bimestre,
        "usuarios": usuarios,
        "frequencias": frequencias,
        "sondagens": sondagens,
        "fechamento": fechamento,
        "conselho_classe": conselho_classe,
    }


def _indisponivel(ano_letivo: int, bimestre: int) -> dict[str, Any]:
    """Contrato degradado: todos os blocos nulos."""
    return _contrato(
        ano_letivo,
        bimestre,
        atualizado_em=None,
        usuarios=None,
        frequencias=None,
        sondagens=None,
        fechamento=None,
        conselho_classe=None,
    )


def obter_metricas(ano_letivo: int, bimestre: int) -> dict[str, Any]:
    """Retorna o contrato de métricas do SGP para o período informado."""
    chave = _chave_cache(ano_letivo, bimestre)
    cacheado: dict[str, Any] | None = cache.get(chave)
    if cacheado is not None:
        return cacheado

    try:
        contrato = _contrato(
            ano_letivo,
            bimestre,
            atualizado_em=timezone.now().isoformat(),
            usuarios=handler.obter_usuarios(),
            frequencias=handler.obter_frequencias(),
            sondagens=handler.obter_sondagens(),
            fechamento=handler.obter_fechamento(ano_letivo, bimestre),
            conselho_classe=handler.obter_conselho_classe(
                ano_letivo, bimestre
            ),
        )
    except psycopg.Error:
        logger.exception("Falha ao coletar métricas do SGP")
        return _indisponivel(ano_letivo, bimestre)

    cache.set(chave, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
