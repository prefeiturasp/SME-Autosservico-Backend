"""Testes dos clientes de leitura dos bancos do GIPE."""

from unittest.mock import patch

from apps.gipe import client


class TestClient:
    def test_cada_banco_usa_o_seu_dsn(self, settings) -> None:
        settings.GIPE_OCORRENCIAS_DSN = "dsn-ocorrencias"
        settings.GIPE_ANEXOS_DSN = "dsn-anexos"
        settings.GIPE_USUARIOS_DSN = "dsn-usuarios"

        with patch(
            "apps.gipe.client.executar_consulta_leitura",
            return_value=[{"total": 1}],
        ) as executar:
            ocorrencias = client.consultar_ocorrencias("select 1", {"x": 1})
            anexos = client.consultar_anexos("select 3")
            usuarios = client.consultar_usuarios("select 2")

        assert ocorrencias == anexos == usuarios == [{"total": 1}]
        assert [c.args for c in executar.call_args_list] == [
            ("dsn-ocorrencias", "select 1", {"x": 1}),
            ("dsn-anexos", "select 3", ()),
            ("dsn-usuarios", "select 2", ()),
        ]
