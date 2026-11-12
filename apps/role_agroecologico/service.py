"""Serviço de métricas do Rolê Agroecológico."""

import logging
import time
from datetime import datetime
from typing import Any

import pymysql
from django.core.cache import cache
from django.utils import timezone

from apps.role_agroecologico import handler

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600

CHAVE_CACHE = "role_agroecologico:metricas"


def _agora_local() -> datetime:
    """Agora no fuso do projeto, sem tzinfo.

    O WordPress grava ``post_date`` em hora local, sem fuso.
    """
    return timezone.localtime().replace(tzinfo=None)


def _contrato(
    *,
    atualizado_em: str | None,
    participacao: dict[str, Any] | None,
    unidades_produtivas: dict[str, Any] | None,
    agendamentos: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do Rolê Agroecológico."""
    return {
        "atualizado_em": atualizado_em,
        "indicadores_participacao_logistica": participacao,
        "unidades_produtivas": unidades_produtivas,
        "agendamentos_roles": agendamentos,
    }


def obter_metricas() -> dict[str, Any]:
    """Retorna o contrato de métricas do Rolê Agroecológico.

    O painel não tem seletor de período: tudo é a fotografia do momento.
    """
    cacheado: dict[str, Any] | None = cache.get(CHAVE_CACHE)
    if cacheado is not None:
        return cacheado

    inicio_coleta = time.monotonic()
    try:
        inscricoes = handler.obter_inscricoes()
        contrato = _contrato(
            atualizado_em=timezone.now().isoformat(),
            participacao=handler.obter_participacao_logistica(inscricoes),
            unidades_produtivas=handler.obter_unidades_produtivas(inscricoes),
            agendamentos=handler.obter_agendamentos_roles(
                inscricoes, _agora_local()
            ),
        )
    except pymysql.MySQLError:
        logger.exception("Falha ao coletar métricas do Rolê Agroecológico")
        return _contrato(
            atualizado_em=None,
            participacao=None,
            unidades_produtivas=None,
            agendamentos=None,
        )

    logger.info(
        "Métricas do Rolê Agroecológico coletadas em %.0f ms",
        (time.monotonic() - inicio_coleta) * 1000,
    )
    cache.set(CHAVE_CACHE, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
