"""Cliente de leitura do banco do Bens Físicos."""

from collections.abc import Mapping
from typing import Any

from django.conf import settings

from apps.core.postgres_leitura import executar_consulta_leitura

Params = tuple[Any, ...] | Mapping[str, Any]


def consultar(query: str, params: Params = ()) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco do Bens Físicos."""
    return executar_consulta_leitura(settings.BENS_FISICOS_DSN, query, params)
