"""Leitura somente-leitura de bancos MySQL de sistemas externos."""

import logging
import time
from collections.abc import Mapping
from typing import Any

import environ
import pymysql
from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)

_TENTATIVAS_PADRAO = 3
_BACKOFF_BASE_SEGUNDOS = 0.5
_PORTA_PADRAO = 3306
_CONNECT_TIMEOUT_SEGUNDOS = 5
_READ_TIMEOUT_SEGUNDOS = 30


def _parametros_conexao(connection_string: str) -> dict[str, Any]:
    config = environ.Env.db_url_config(connection_string)
    return {
        "host": config["HOST"],
        "port": int(config["PORT"] or _PORTA_PADRAO),
        "user": config["USER"],
        "password": config["PASSWORD"],
        "database": config["NAME"],
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "connect_timeout": _CONNECT_TIMEOUT_SEGUNDOS,
        "read_timeout": _READ_TIMEOUT_SEGUNDOS,
    }


def executar_consulta_leitura(
    connection_string: str,
    query: str,
    params: tuple[Any, ...] | Mapping[str, Any] = (),
    tentativas: int = _TENTATIVAS_PADRAO,
) -> list[dict[str, Any]]:
    """Executa uma consulta somente-leitura, com retry e backoff.

    O ``pymysql`` sempre formata a query com ``%`` quando há parâmetros,
    então ``%`` literal na query precisa ser escrito como ``%%``.
    """
    parametros = _parametros_conexao(connection_string)
    ultimo_erro: pymysql.err.OperationalError | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            with (
                pymysql.connect(**parametros) as conexao,
                conexao.cursor() as cursor,
            ):
                cursor.execute(query, params)
                return list(cursor.fetchall())
        except pymysql.err.OperationalError as erro:
            ultimo_erro = erro
            logger.warning(
                "Falha de conexão ao MySQL (tentativa %s de %s): %s",
                tentativa,
                tentativas,
                erro,
            )
            if tentativa < tentativas:
                atraso = _BACKOFF_BASE_SEGUNDOS * 2 ** (tentativa - 1)
                time.sleep(atraso)
    raise ultimo_erro  # type: ignore[misc]
