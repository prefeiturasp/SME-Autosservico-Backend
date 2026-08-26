"""Serviço de métricas do SIGPAE."""

import logging
from typing import Any

import psycopg
from django.core.cache import cache
from django.utils import timezone

from apps.sigpae import handler

logger = logging.getLogger(__name__)

_CHAVE_CACHE_USUARIOS = "sigpae:metricas:usuarios"
CACHE_TTL_USUARIOS_SEGUNDOS = 300


def _usuarios_indisponivel() -> dict[str, Any]:
    """Bloco ``usuarios`` com todos os indicadores nulos."""
    return {
        "com_acesso_ativo": None,
        "unicos_por_dia": None,
        "acessos_hoje": None,
        "por_tipo_perfil": {
            "codae": None,
            "dre": None,
            "ue": None,
            "empresa": None,
        },
        "comparativo_acessos": None,
    }


def obter_metricas() -> dict[str, Any]:
    """Retorna o contrato de métricas do SIGPAE."""
    consolidado = cache.get(_CHAVE_CACHE_USUARIOS)
    if consolidado is None:
        try:
            consolidado = {
                "usuarios": handler.obter_usuarios(),
                "atualizado_em": timezone.now().isoformat(),
            }
        except psycopg.Error:
            logger.exception("Falha ao coletar métricas de usuários do SIGPAE")
            return {
                "atualizado_em": None,
                "usuarios": _usuarios_indisponivel(),
            }
        cache.set(
            _CHAVE_CACHE_USUARIOS,
            consolidado,
            CACHE_TTL_USUARIOS_SEGUNDOS,
        )
    return {
        "atualizado_em": consolidado["atualizado_em"],
        "usuarios": consolidado["usuarios"],
    }
