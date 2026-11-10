"""Serviço de métricas do Bens Físicos."""

import logging
import time
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.bensfisicos import handler

logger = logging.getLogger(__name__)

CHAVE_CACHE = "bensfisicos:metricas"
CACHE_TTL_SEGUNDOS = 3600


def _contrato(
    *,
    atualizado_em: str | None,
    usuarios: dict[str, Any] | None,
    cadastro_de_bens: dict[str, Any] | None,
    baixas_fisicas: dict[str, Any] | None,
    movimentacoes: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do Bens Físicos."""
    return {
        "atualizado_em": atualizado_em,
        "usuarios": usuarios,
        "cadastro_de_bens": cadastro_de_bens,
        "baixas_fisicas": baixas_fisicas,
        "movimentacoes": movimentacoes,
    }


def obter_metricas() -> dict[str, Any]:
    """Retorna o contrato de métricas do Bens Físicos (fotografia atual).

    Se o banco falhar, devolve os blocos nulos e não grava o cache.
    """
    cacheado: dict[str, Any] | None = cache.get(CHAVE_CACHE)
    if cacheado is not None:
        return cacheado

    inicio_coleta = time.monotonic()
    try:
        contrato = _contrato(
            atualizado_em=timezone.now().isoformat(),
            usuarios=handler.obter_usuarios(),
            cadastro_de_bens=handler.obter_cadastro_de_bens(),
            baixas_fisicas=handler.obter_baixas_fisicas(),
            movimentacoes=handler.obter_movimentacoes(),
        )
    except psycopg.Error:
        logger.exception("Falha ao coletar métricas do Bens Físicos")
        return _contrato(
            atualizado_em=None,
            usuarios=None,
            cadastro_de_bens=None,
            baixas_fisicas=None,
            movimentacoes=None,
        )

    logger.info(
        "Métricas do Bens Físicos coletadas em %.0f ms",
        (time.monotonic() - inicio_coleta) * 1000,
    )
    cache.set(CHAVE_CACHE, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
