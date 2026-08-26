"""Cliente de leitura do banco do SIGPAE.

Fina camada sobre ``apps.core.postgres_leitura`` que injeta a connection
string do SIGPAE (``settings.SIGPAE_DSN``).
"""

from typing import Any

from django.conf import settings

from apps.core.postgres_leitura import executar_consulta_leitura


def consultar(
    query: str, params: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco do SIGPAE.

    Args:
        query: Consulta SQL a executar.
        params: Parâmetros posicionais da consulta, se houver.

    Returns:
        As linhas retornadas, cada uma como um dicionário coluna→valor.
    """
    return executar_consulta_leitura(settings.SIGPAE_DSN, query, params)
