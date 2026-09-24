"""Leitura somente-leitura de bancos PostgreSQL de sistemas externos."""

import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

_TENTATIVAS_PADRAO = 3
_BACKOFF_BASE_SEGUNDOS = 0.5


def executar_consulta_leitura(
    connection_string: str,
    query: str,
    params: tuple[Any, ...] = (),
    tentativas: int = _TENTATIVAS_PADRAO,
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura, com retry e backoff."""
    ultimo_erro: psycopg.OperationalError | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            with (
                psycopg.connect(
                    connection_string, row_factory=dict_row
                ) as conexao,
                conexao.cursor() as cursor,
            ):
                cursor.execute(query, params)
                return cursor.fetchall()
        except psycopg.OperationalError as erro:
            ultimo_erro = erro
            if tentativa < tentativas:
                atraso = _BACKOFF_BASE_SEGUNDOS * 2 ** (tentativa - 1)
                time.sleep(atraso)
    raise ultimo_erro  # type: ignore[misc]
