"""Testes do cliente de leitura do banco do Intranet."""

from unittest.mock import patch

from apps.intranet import client


class TestClient:
    """Cobre o repasse ao helper MySQL compartilhado."""

    def test_usa_dsn_do_intranet(self, settings) -> None:
        """A consulta usa ``INTRANET_DSN`` e repassa os parâmetros."""
        settings.INTRANET_DSN = "mysql://intranet-db/intranet"

        with patch(
            "apps.intranet.client.executar_consulta_leitura",
            return_value=[{"total": 1}],
        ) as executar:
            linhas = client.consultar("select %(x)s", {"x": 1})

        assert linhas == [{"total": 1}]
        executar.assert_called_once_with(
            "mysql://intranet-db/intranet", "select %(x)s", {"x": 1}
        )
