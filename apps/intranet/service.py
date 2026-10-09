"""Serviço de métricas do Intranet."""

import logging
import time
from datetime import datetime
from datetime import timedelta
from typing import Any

import pymysql
from django.core.cache import cache
from django.utils import timezone

from apps.intranet import handler
from apps.intranet.handler import Janela

logger = logging.getLogger(__name__)

CACHE_TTL_SEGUNDOS = 3600

PERIODO_GERAL = "geral"

# Janela móvel em dias de cada período do seletor do frontend. ``dia``
# não entra aqui: é recortado a partir da meia-noite de hoje.
_DIAS_POR_PERIODO = {"quinzena": 15, "mes": 30, "trimestre": 90}

PERIODOS = (PERIODO_GERAL, "dia", *_DIAS_POR_PERIODO)


def _agora_local() -> datetime:
    """Agora no fuso do projeto, sem tzinfo.

    O WordPress grava ``data_inscricao`` em hora local, sem fuso.
    """
    return timezone.localtime().replace(tzinfo=None)


def _janela_periodo(periodo: str) -> Janela:
    """Converte o ``periodo`` do seletor numa janela de datas móvel."""
    if periodo == "dia":
        inicio = _agora_local().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return {"inicio": inicio, "fim": None}
    dias = _DIAS_POR_PERIODO.get(periodo)
    if dias is None:
        return {"inicio": None, "fim": None}
    return {"inicio": _agora_local() - timedelta(days=dias), "fim": None}


def _janela_mes(mes: str | None) -> Janela:
    """Converte ``AAAA-MM`` no intervalo do mês (fim exclusivo)."""
    if mes is None:
        return {"inicio": None, "fim": None}
    inicio = datetime.strptime(mes, "%Y-%m")
    if inicio.month == 12:
        fim = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fim = inicio.replace(month=inicio.month + 1)
    return {"inicio": inicio, "fim": fim}


def _chave_cache(periodo: str, mes: str | None) -> str:
    """Chave de cache do contrato, por período e mês."""
    return f"intranet:metricas:{periodo}:{mes or PERIODO_GERAL}"


def _contrato(
    periodo: str,
    mes: str | None,
    *,
    atualizado_em: str | None,
    kpis: dict[str, Any] | None,
    sorteios: dict[str, Any] | None,
    ordem_inscricao: dict[str, Any] | None,
    oportunidades: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do Intranet."""
    return {
        "atualizado_em": atualizado_em,
        "periodo": periodo,
        "mes": mes,
        "kpis": kpis,
        "sorteios": sorteios,
        "ordem_inscricao": ordem_inscricao,
        "oportunidades": oportunidades,
    }


def obter_metricas(
    periodo: str = PERIODO_GERAL, mes: str | None = None
) -> dict[str, Any]:
    """Retorna o contrato de métricas do Intranet.

    Args:
        periodo: Recorte dos cards por tipo/ganhador/DRE (um de
            ``PERIODOS``); ``geral`` não filtra por data.
        mes: Mês ``AAAA-MM`` do card "por DRE" de Ordem de Inscrição;
            ``None`` não filtra por data.
    """
    chave = _chave_cache(periodo, mes)
    cacheado: dict[str, Any] | None = cache.get(chave)
    if cacheado is not None:
        return cacheado

    janela = _janela_periodo(periodo)
    inicio_coleta = time.monotonic()
    try:
        contrato = _contrato(
            periodo,
            mes,
            atualizado_em=timezone.now().isoformat(),
            kpis=handler.obter_kpis(),
            sorteios=handler.obter_sorteios(janela),
            ordem_inscricao=handler.obter_ordem_inscricao(
                janela, _janela_mes(mes)
            ),
            oportunidades=handler.obter_oportunidades(),
        )
    except pymysql.MySQLError:
        logger.exception("Falha ao coletar métricas do Intranet")
        return _contrato(
            periodo,
            mes,
            atualizado_em=None,
            kpis=None,
            sorteios=None,
            ordem_inscricao=None,
            oportunidades=None,
        )

    logger.info(
        "Métricas do Intranet coletadas em %.0f ms (periodo=%s, mes=%s)",
        (time.monotonic() - inicio_coleta) * 1000,
        periodo,
        mes,
    )
    cache.set(chave, contrato, CACHE_TTL_SEGUNDOS)
    return contrato
