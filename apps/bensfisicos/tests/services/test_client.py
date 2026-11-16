"""Testes do cliente de leitura do banco do Bens Físicos."""

from unittest.mock import patch

from apps.bensfisicos import client


class TestClient:
    def test_usa_a_dsn_do_bens_fisicos(self, settings) -> None:
        settings.BENS_FISICOS_DSN = "dsn-bens"

        with patch(
            "apps.bensfisicos.client.executar_consulta_leitura",
            return_value=[{"total": 1}],
        ) as executar:
            linhas = client.consultar("select 1", {"x": 1})

        assert linhas == [{"total": 1}]
        executar.assert_called_once_with("dsn-bens", "select 1", {"x": 1})
