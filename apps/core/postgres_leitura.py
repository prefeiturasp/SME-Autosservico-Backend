"""Leitura somente-leitura de bancos PostgreSQL de sistemas externos.

Infraestrutura genérica reaproveitável por qualquer domínio que precise
ler (nunca escrever) dados relacionais de um sistema legado da SME. Não
usa ORM/migrations: quem chama já traz a connection string e o SQL
prontos.

Cada tentativa abre e fecha a própria conexão. Falhas de conexão são
retentadas com backoff exponencial; erros de sintaxe/permissão do SQL
não são retentados, pois não se resolvem sozinhos.
"""

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
    """Executa uma consulta SQL somente-leitura num banco externo.

    Args:
        connection_string: String de conexão de um usuário com permissão
            apenas de ``SELECT``. Deve incluir ``connect_timeout`` para
            limitar o tempo de indisponibilidade.
        query: Consulta SQL a executar.
        params: Parâmetros posicionais da consulta, se houver.
        tentativas: Número máximo de tentativas em caso de falha de
            conexão.

    Returns:
        As linhas retornadas, cada uma como um dicionário coluna→valor.

    Raises:
        psycopg.OperationalError: Se todas as tentativas de conexão
            falharem.
    """
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
