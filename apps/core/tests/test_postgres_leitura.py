"""Testes do cliente de leitura de bancos PostgreSQL externos."""

import secrets
from unittest.mock import MagicMock
from unittest.mock import patch
from urllib.parse import urlunsplit

import psycopg
import pytest

from apps.core.postgres_leitura import _dsn_sem_parametros_quebrados
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

    def test_abre_a_sessao_em_modo_somente_leitura(self) -> None:
        """A sessão é read_only, mesmo que o usuário possa escrever."""
        cm_conexao, _ = _conexao_mock([])

        with patch(
            "apps.core.postgres_leitura.psycopg.connect",
            return_value=cm_conexao,
        ):
            executar_consulta_leitura("dsn", "select 1")

        assert cm_conexao.__enter__.return_value.read_only is True

    def test_aceita_parametros_nomeados(self) -> None:
        """Um dicionário de parâmetros chega intacto ao cursor."""
        cm_conexao, cursor = _conexao_mock([])
        params = {"dre": "108100"}

        with patch(
            "apps.core.postgres_leitura.psycopg.connect",
            return_value=cm_conexao,
        ):
            executar_consulta_leitura("dsn", "select %(dre)s", params)

        cursor.execute.assert_called_once_with("select %(dre)s", params)


def _dsn(query: str = "") -> str:
    """Monta uma DSN URI de teste com senha aleatória.

    A DSN é montada aqui, e não escrita como literal, para que o Sonar não
    a confunda com credencial real nem com banco sem senha. O ``%40`` na
    senha cobre o escape que as DSNs reais usam.
    """
    senha = f"{secrets.token_hex(4)}%40"
    return urlunsplit(
        ("postgresql", f"usuario:{senha}@h:5432", "/db", query, "")
    )


class TestDsnSemParametrosQuebrados:
    """Cobre a limpeza de DSN cortada no ``=`` pela ferramenta de deploy."""

    def test_remove_parametro_sem_valor(self) -> None:
        """``?sslmode`` sem ``=`` é descartado e o resto da DSN fica igual."""
        dsn = _dsn("sslmode")

        assert _dsn_sem_parametros_quebrados(dsn) == dsn.removesuffix(
            "?sslmode"
        )

    def test_mantem_parametros_validos(self) -> None:
        """Só o parâmetro sem ``=`` sai; os válidos continuam na ordem."""
        dsn = _dsn("sslmode&connect_timeout=5")

        assert _dsn_sem_parametros_quebrados(dsn) == dsn.replace(
            "?sslmode&", "?"
        )

    def test_dsn_correta_nao_muda(self) -> None:
        """Uma DSN bem formada passa intacta."""
        dsn = _dsn("sslmode=prefer&connect_timeout=5")

        assert _dsn_sem_parametros_quebrados(dsn) == dsn

    def test_dsn_chave_valor_nao_muda(self) -> None:
        """O formato ``host=... dbname=...`` não é URL e passa intacto."""
        dsn = "host=h port=5432 dbname=db user=usuario"

        assert _dsn_sem_parametros_quebrados(dsn) == dsn

    def test_connect_recebe_a_dsn_limpa(self) -> None:
        """O gateway conecta com a DSN já sem o parâmetro quebrado."""
        cm_conexao, _ = _conexao_mock([])
        dsn = _dsn("sslmode")

        with patch(
            "apps.core.postgres_leitura.psycopg.connect",
            return_value=cm_conexao,
        ) as connect:
            executar_consulta_leitura(dsn, "select 1")

        assert connect.call_args.args[0] == dsn.removesuffix("?sslmode")
