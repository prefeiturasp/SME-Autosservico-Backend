"""Cliente de leitura do banco do Rolê Agroecológico."""

from collections.abc import Mapping
from typing import Any

from django.conf import settings

from apps.core.mysql_leitura import executar_consulta_leitura


def consultar(
    query: str, params: tuple[Any, ...] | Mapping[str, Any] = ()
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura no banco do Rolê."""
    return executar_consulta_leitura(settings.ROLE_AGRO_DSN, query, params)
