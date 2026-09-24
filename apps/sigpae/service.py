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


def _medicoes_indisponivel() -> dict[str, Any]:
    """Bloco ``medicoes_iniciais`` com todas as categorias nulas."""
    return {
        "aguardando_envio_ue": None,
        "enviadas_pelas_unidades": None,
        "aprovadas_pelas_dres": None,
        "aguardando_codae": None,
        "aprovadas_codae": None,
    }


def _logistica_indisponivel() -> dict[str, Any]:
    """Bloco ``logistica`` com todos os cards nulos."""
    return {
        "cronogramas_entregas": None,
        "fichas_tecnicas_produtos": None,
        "fornecedores_distribuidores": None,
        "layouts_embalagens": None,
    }


def _contrato(
    usuarios: dict[str, Any],
    medicoes_iniciais: dict[str, Any],
    produtos_homologados: dict[str, Any] | None,
    empresas_terceirizadas: dict[str, Any] | None,
    solicitacoes_dietas_especiais: dict[str, Any] | None,
    solicitacoes_alimentacoes: dict[str, Any] | None,
    logistica: dict[str, Any],
    atualizado_em: str | None,
) -> dict[str, Any]:
    """Monta o contrato de métricas do SIGPAE."""
    return {
        "atualizado_em": atualizado_em,
        "usuarios": usuarios,
        "alimentacao_terceirizada": {
            "medicoes_iniciais": medicoes_iniciais,
            "produtos_homologados": produtos_homologados,
            "empresas_terceirizadas": empresas_terceirizadas,
            "solicitacoes_dietas_especiais": solicitacoes_dietas_especiais,
            "solicitacoes_alimentacoes": solicitacoes_alimentacoes,
        },
        "logistica": logistica,
    }


def obter_metricas() -> dict[str, Any]:
    """Retorna o contrato de métricas do SIGPAE."""
    consolidado = cache.get(_CHAVE_CACHE_USUARIOS)
    if consolidado is None:
        try:
            consolidado = {
                "usuarios": handler.obter_usuarios(),
                "medicoes_iniciais": handler.obter_medicoes_iniciais(),
                "produtos_homologados": handler.obter_produtos_homologados(),
                "empresas_terceirizadas": (
                    handler.obter_empresas_terceirizadas()
                ),
                "solicitacoes_dietas_especiais": (
                    handler.obter_solicitacoes_dietas_especiais()
                ),
                "solicitacoes_alimentacoes": (
                    handler.obter_solicitacoes_alimentacoes()
                ),
                "logistica": {
                    "cronogramas_entregas": (
                        handler.obter_cronogramas_entregas()
                    ),
                    "fichas_tecnicas_produtos": (
                        handler.obter_fichas_tecnicas_produtos()
                    ),
                    "fornecedores_distribuidores": (
                        handler.obter_fornecedores_distribuidores()
                    ),
                    "layouts_embalagens": (handler.obter_layouts_embalagens()),
                },
                "atualizado_em": timezone.now().isoformat(),
            }
        except psycopg.Error:
            logger.exception("Falha ao coletar métricas do SIGPAE")
            return _contrato(
                _usuarios_indisponivel(),
                _medicoes_indisponivel(),
                None,
                None,
                None,
                None,
                _logistica_indisponivel(),
                None,
            )
        cache.set(
            _CHAVE_CACHE_USUARIOS,
            consolidado,
            CACHE_TTL_USUARIOS_SEGUNDOS,
        )
    return _contrato(
        consolidado["usuarios"],
        consolidado["medicoes_iniciais"],
        consolidado["produtos_homologados"],
        consolidado["empresas_terceirizadas"],
        consolidado["solicitacoes_dietas_especiais"],
        consolidado["solicitacoes_alimentacoes"],
        consolidado["logistica"],
        consolidado["atualizado_em"],
    )
