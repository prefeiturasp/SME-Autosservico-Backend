"""Testes do cliente de leitura e do prefixo das tabelas do Rolê."""

from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.role_agroecologico import client
from apps.role_agroecologico import queries


class TestClient:
    def test_usa_dsn_do_role(self, settings) -> None:
        settings.ROLE_AGRO_DSN = "dsn-role"

        with patch(
            "apps.role_agroecologico.client.executar_consulta_leitura",
            return_value=[{"total": 1}],
        ) as executar:
            linhas = client.consultar("select 1")

        assert linhas == [{"total": 1}]
        executar.assert_called_once_with("dsn-role", "select 1", ())


class TestPrefixoTabelas:
    @pytest.mark.parametrize("prefixo", ["hom_wp_", "dev_wp_", "wp_"])
    def test_prefixo_valido(self, settings, prefixo: str) -> None:
        settings.ROLE_AGRO_PREFIXO_TABELAS = prefixo

        assert queries.prefixo_tabelas() == prefixo

    @pytest.mark.parametrize(
        "prefixo", ["", "hom_wp_; drop table x;", "hom wp_", "hóm_"]
    )
    def test_prefixo_invalido(self, settings, prefixo: str) -> None:
        settings.ROLE_AGRO_PREFIXO_TABELAS = prefixo

        with pytest.raises(ImproperlyConfigured):
            queries.prefixo_tabelas()
