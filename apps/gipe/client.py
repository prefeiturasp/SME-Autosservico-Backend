"""Clientes de leitura dos três bancos do GIPE."""

from collections.abc import Mapping
from typing import Any

from django.conf import settings

from apps.core.postgres_leitura import executar_consulta_leitura

Params = tuple[Any, ...] | Mapping[str, Any]


def consultar_ocorrencias(
    query: str, params: Params = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco de ocorrências."""
    return executar_consulta_leitura(
        settings.GIPE_OCORRENCIAS_DSN, query, params
    )


def consultar_anexos(query: str, params: Params = ()) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco de anexos."""
    return executar_consulta_leitura(settings.GIPE_ANEXOS_DSN, query, params)


def consultar_usuarios(
    query: str, params: Params = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco de usuários."""
    return executar_consulta_leitura(settings.GIPE_USUARIOS_DSN, query, params)
