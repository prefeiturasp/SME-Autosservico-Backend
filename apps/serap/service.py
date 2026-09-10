"""Serviço de métricas de provas do SERAp Estudantes."""

import logging
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.serap import handler

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600

# ponytail: mapa (ano, bimestre) -> (inicio, fim) ainda vazio, à espera do
# calendário oficial dos bimestres. Sem janela, os números vêm globais (não
# recortados por bimestre). Preencher aqui quando o PO definir as datas.
_JANELA_BIMESTRE: dict[tuple[int, int], tuple[str, str]] = {}


def _janela(ano: int, bimestre: int) -> tuple[str, str] | None:
    """Resolve a janela de datas do bimestre, ou ``None`` se indefinida."""
    return _JANELA_BIMESTRE.get((ano, bimestre))


def _chave_cache(ano: int, bimestre: int) -> str:
    """Chave de cache do contrato, por ano e bimestre."""
    return f"serap:provas:{ano}:{bimestre}"


def _contrato(
    ano: int,
    bimestre: int,
    *,
    atualizado_em: str | None,
    provas: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas de provas do SERAp."""
    return {
        "atualizado_em": atualizado_em,
        "ano": ano,
        "bimestre": bimestre,
        "provas": provas,
    }


def obter_provas(ano: int, bimestre: int) -> dict[str, Any]:
    """Retorna o contrato de métricas de provas para o período."""
    chave = _chave_cache(ano, bimestre)
    cacheado: dict[str, Any] | None = cache.get(chave)
    if cacheado is not None:
        return cacheado

    try:
        contrato = _contrato(
            ano,
            bimestre,
            atualizado_em=timezone.now().isoformat(),
            provas=handler.obter_provas(_janela(ano, bimestre)),
        )
    except psycopg.Error:
        logger.exception("Falha ao coletar métricas de provas do SERAp")
        return _contrato(ano, bimestre, atualizado_em=None, provas=None)

    cache.set(chave, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
