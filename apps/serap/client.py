"""Cliente de leitura do banco do SERAp Estudantes."""

from typing import Any

from django.conf import settings

from apps.core.postgres_leitura import executar_consulta_leitura


def consultar(
    query: str, params: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco do SERAp."""
    return executar_consulta_leitura(
        settings.SERAP_ESTUDANTES_DSN, query, params
    )
