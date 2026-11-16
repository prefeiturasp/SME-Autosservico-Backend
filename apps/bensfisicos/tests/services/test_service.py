"""Testes do cache e da degradação do serviço do Bens Físicos."""

from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.bensfisicos import service

DEGRADADO = {
    "atualizado_em": None,
    "usuarios": None,
    "cadastro_de_bens": None,
    "baixas_fisicas": None,
    "movimentacoes": None,
}


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    cache.clear()


class TestService:
    def test_sucesso_monta_contrato_e_cacheia(self, banco: list[str]) -> None:
        contrato = service.obter_metricas()

        assert contrato["atualizado_em"] is not None
        assert contrato["usuarios"] == {
            "com_acesso_ativo": {"valor": 6},
            "unicos_por_dia": {
                "valor": 1,
                "variacao_percentual_30_dias": 233.3,
            },
        }
        assert contrato["cadastro_de_bens"]["bens_cadastrados"] == 6083
        assert contrato["cadastro_de_bens"]["aguardando_aprovacao"] == 53
        assert contrato["cadastro_de_bens"]["por_unidade_administrativa"][
            0
        ] == {
            "sigla": "SMECOTIC",
            "nome": "COORDENADORIA DE TECNOLOGIA",
            "bens": 493,
        }
        assert contrato["baixas_fisicas"] == {
            "aprovadas": 42,
            "aguardando_aprovacao": 0,
        }
        assert contrato["movimentacoes"] == {
            "realizadas": 1461,
            "pendentes": 80,
            "transferencias_realizadas": 7,
        }

        total_chamadas = len(banco)
        assert service.obter_metricas() == contrato
        assert len(banco) == total_chamadas

    def test_falha_do_banco_degrada_para_nulos(self) -> None:
        with patch(
            "apps.bensfisicos.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            assert service.obter_metricas() == DEGRADADO

    def test_falha_nao_e_cacheada(self, banco: list[str]) -> None:
        with patch(
            "apps.bensfisicos.client.consultar",
            side_effect=psycopg.OperationalError("timeout"),
        ):
            service.obter_metricas()

        assert service.obter_metricas()["atualizado_em"] is not None
