"""Testes do cliente de leitura de bancos MySQL externos."""

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pymysql
import pytest

from apps.core.mysql_leitura import executar_consulta_leitura

# O parse da URL é do django-environ; aqui ele é simulado, sem URL de banco
# no código (o Sonar aponta qualquer connection string como segredo).
_DSN = "dsn"
_SENHA = object()


def _config(porta: int | str = 3307) -> dict[str, Any]:
    return {
        "HOST": "intranet-db",
        "PORT": porta,
        "USER": "leitor",
        "PASSWORD": _SENHA,
        "NAME": "intranet_dev",
    }


@pytest.fixture(autouse=True)
def db_url_config():
    with patch(
        "apps.core.mysql_leitura.environ.Env.db_url_config",
        return_value=_config(),
    ) as db_url_config:
        yield db_url_config


def _conexao_mock(linhas: list[dict]) -> tuple[MagicMock, MagicMock]:
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
    def test_retorna_linhas_e_repassa_params(self) -> None:
        cm_conexao, cursor = _conexao_mock([{"total": 1}])

        with patch(
            "apps.core.mysql_leitura.pymysql.connect",
            return_value=cm_conexao,
        ):
            linhas = executar_consulta_leitura(_DSN, "select %(x)s", {"x": 1})

        assert linhas == [{"total": 1}]
        cursor.execute.assert_called_once_with("select %(x)s", {"x": 1})

    def test_converte_dsn_em_parametros_com_timeouts(
        self, db_url_config: MagicMock
    ) -> None:
        cm_conexao, _ = _conexao_mock([])

        with patch(
            "apps.core.mysql_leitura.pymysql.connect",
            return_value=cm_conexao,
        ) as connect:
            executar_consulta_leitura(_DSN, "select 1")

        db_url_config.assert_called_once_with(_DSN)
        kwargs = connect.call_args.kwargs
        assert kwargs["host"] == "intranet-db"
        assert kwargs["port"] == 3307
        assert kwargs["user"] == "leitor"
        assert kwargs["password"] is _SENHA
        assert kwargs["database"] == "intranet_dev"
        assert kwargs["connect_timeout"] > 0
        assert kwargs["read_timeout"] > 0

    def test_porta_padrao_quando_ausente(
        self, db_url_config: MagicMock
    ) -> None:
        db_url_config.return_value = _config(porta="")
        cm_conexao, _ = _conexao_mock([])

        with patch(
            "apps.core.mysql_leitura.pymysql.connect",
            return_value=cm_conexao,
        ) as connect:
            executar_consulta_leitura(_DSN, "select 1")

        assert connect.call_args.kwargs["port"] == 3306

    def test_retenta_apos_falha_de_conexao(self) -> None:
        cm_conexao, _ = _conexao_mock([])

        with (
            patch("apps.core.mysql_leitura.time.sleep"),
            patch(
                "apps.core.mysql_leitura.pymysql.connect",
                side_effect=[pymysql.err.OperationalError("x"), cm_conexao],
            ) as connect,
        ):
            executar_consulta_leitura(_DSN, "select 1")

        assert connect.call_count == 2

    def test_esgota_tentativas_e_relanca(self) -> None:
        with (
            patch("apps.core.mysql_leitura.time.sleep"),
            patch(
                "apps.core.mysql_leitura.pymysql.connect",
                side_effect=pymysql.err.OperationalError("down"),
            ),
            pytest.raises(pymysql.err.OperationalError),
        ):
            executar_consulta_leitura(_DSN, "select 1", tentativas=2)
