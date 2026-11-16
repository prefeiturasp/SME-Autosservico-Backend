"""Testes do cache e da degradação do serviço do Rolê."""

from unittest.mock import patch

import pymysql
import pytest
from django.core.cache import cache

from apps.role_agroecologico import service
from apps.role_agroecologico.tests.conftest import Banco


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    cache.clear()


class TestService:
    def test_sucesso_monta_contrato_e_cacheia(self, banco: Banco) -> None:
        contrato = service.obter_metricas()

        assert contrato["atualizado_em"] is not None
        participacao = contrato["indicadores_participacao_logistica"]
        assert participacao["vivencias_realizadas"] == 2
        assert contrato["unidades_produtivas"]["ups_cadastradas"] == 3
        assert contrato["agendamentos_roles"]["agendamentos_totais"] == 4
        # Inscrições alimentam os três blocos, mas são lidas uma vez só.
        assert len(banco.consultas) == 2

        service.obter_metricas()
        assert len(banco.consultas) == 2

    def test_falha_degrada_para_nulos(self, banco: Banco) -> None:
        with patch(
            "apps.role_agroecologico.client.consultar",
            side_effect=pymysql.err.OperationalError(2003, "indisponivel"),
        ):
            contrato = service.obter_metricas()

        assert contrato == {
            "atualizado_em": None,
            "indicadores_participacao_logistica": None,
            "unidades_produtivas": None,
            "agendamentos_roles": None,
        }

    def test_falha_nao_e_cacheada(self, banco: Banco) -> None:
        with patch(
            "apps.role_agroecologico.client.consultar",
            side_effect=pymysql.err.OperationalError(2013, "timeout"),
        ):
            service.obter_metricas()

        assert service.obter_metricas()["atualizado_em"] is not None
