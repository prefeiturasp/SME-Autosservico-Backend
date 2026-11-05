"""Serviço de métricas do GIPE."""

import logging
import time
from datetime import date
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.gipe import handler

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600


def janela_do_ano(ano_letivo: int) -> handler.Janela:
    """Ano letivo como janela de datas: 1/jan até 1/jan do ano seguinte."""
    return {
        "inicio": date(ano_letivo, 1, 1),
        "fim": date(ano_letivo + 1, 1, 1),
    }


def _chave_cache(ano_letivo: int) -> str:
    """Chave de cache do contrato, por ano letivo."""
    return f"gipe:metricas:{ano_letivo}"


def _contrato(
    ano_letivo: int,
    *,
    atualizado_em: str | None,
    kpis: dict[str, Any] | None,
    ocorrencias: dict[str, Any] | None,
    usuarios: dict[str, Any] | None,
    produtividade: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do GIPE."""
    return {
        "atualizado_em": atualizado_em,
        "ano_letivo": ano_letivo,
        "kpis": kpis,
        "ocorrencias": ocorrencias,
        "usuarios": usuarios,
        "produtividade": produtividade,
    }


def obter_metricas(ano_letivo: int) -> dict[str, Any]:
    """Retorna o contrato de métricas do GIPE para o ano letivo.

    KPIs, o bloco ``usuarios``, "sem movimentação há 7 dias" e anexos são
    a fotografia do momento; os demais cards de ocorrências são do ano.
    """
    chave = _chave_cache(ano_letivo)
    cacheado: dict[str, Any] | None = cache.get(chave)
    if cacheado is not None:
        return cacheado

    janela = janela_do_ano(ano_letivo)
    inicio_coleta = time.monotonic()
    try:
        movimentacoes = handler.obter_movimentacoes(janela)
        contrato = _contrato(
            ano_letivo,
            atualizado_em=timezone.now().isoformat(),
            kpis=handler.obter_kpis(),
            ocorrencias=handler.obter_ocorrencias(janela, movimentacoes),
            usuarios=handler.obter_usuarios(),
            produtividade=handler.obter_produtividade(movimentacoes),
        )
    except psycopg.Error:
        logger.exception("Falha ao coletar métricas do GIPE")
        return _contrato(
            ano_letivo,
            atualizado_em=None,
            kpis=None,
            ocorrencias=None,
            usuarios=None,
            produtividade=None,
        )

    logger.info(
        "Métricas do GIPE coletadas em %.0f ms (ano_letivo=%s)",
        (time.monotonic() - inicio_coleta) * 1000,
        ano_letivo,
    )
    cache.set(chave, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
