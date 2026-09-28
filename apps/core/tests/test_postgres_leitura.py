"""Testes do cliente de leitura de bancos PostgreSQL externos."""

from unittest.mock import MagicMock
from unittest.mock import patch

import psycopg
import pytest

from apps.core.postgres_leitura import executar_consulta_leitura


def _conexao_mock(linhas: list[dict]) -> tuple[MagicMock, MagicMock]:
    """Monta um mock de conexão/cursor no formato de context manager.

    Args:
        linhas: Linhas que ``cursor.fetchall`` deve retornar.

    Returns:
        A tupla ``(retorno_de_connect, cursor)``.
    """
    cursor = MagicMock()
    cursor.fetchall.return_value = linhas
    cm_cursor = MagicMock()
    cm_cursor.__enter__.return_value = cursor
    conexao = MagicMock()
    conexao.cursor.return_value = cm_cursor
    cm_conexao = MagicMock()
    cm_conexao.__enter__.return_value = conexao
    return cm_conexao, cursor


class TestExecutarConsultaLeitura:
    """Cobre o cliente genérico de leitura com retry."""

    def test_retorna_linhas_e_repassa_params(self) -> None:
        """A consulta é executada com os parâmetros e retorna as linhas."""
        cm_conexao, cursor = _conexao_mock([{"total": 1}])

        with patch(
            "apps.core.postgres_leitura.psycopg.connect",
            return_value=cm_conexao,
        ):
            linhas = executar_consulta_leitura("dsn", "select 1", ("x",))

        assert linhas == [{"total": 1}]
        cursor.execute.assert_called_once_with("select 1", ("x",))

    def test_retenta_apos_falha_de_conexao(self) -> None:
        """Uma falha transitória é retentada até obter sucesso."""
        cm_conexao, _ = _conexao_mock([])

        with (
            patch("apps.core.postgres_leitura.time.sleep"),
            patch(
                "apps.core.postgres_leitura.psycopg.connect",
                side_effect=[psycopg.OperationalError("x"), cm_conexao],
            ) as connect,
        ):
            executar_consulta_leitura("dsn", "select 1")

        assert connect.call_count == 2

    def test_esgota_tentativas_e_relanca(self) -> None:
        """Esgotadas as tentativas, o erro de conexão é propagado."""
        with (
            patch("apps.core.postgres_leitura.time.sleep"),
            patch(
                "apps.core.postgres_leitura.psycopg.connect",
                side_effect=psycopg.OperationalError("down"),
            ),
            pytest.raises(psycopg.OperationalError),
        ):
            executar_consulta_leitura("dsn", "select 1", tentativas=2)
