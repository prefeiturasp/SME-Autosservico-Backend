"""Cliente de leitura do banco do SIG-Escola (PTRF)."""

from collections.abc import Mapping
from typing import Any

from django.conf import settings

from apps.core.postgres_leitura import executar_consulta_leitura


def consultar(
    query: str, params: tuple[Any, ...] | Mapping[str, Any] = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco do SIG-Escola."""
    return executar_consulta_leitura(settings.SIGESCOLA_DSN, query, params)
