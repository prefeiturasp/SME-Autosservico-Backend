"""Cliente de leitura do banco do SGP."""

from typing import Any

from django.conf import settings

from apps.core.postgres_leitura import executar_consulta_leitura


def consultar(
    query: str, params: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco do SGP."""
    return executar_consulta_leitura(settings.SGP_DSN, query, params)
