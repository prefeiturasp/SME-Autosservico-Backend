"""Testes da janela do ano, do cache e da degradação do serviço."""

from datetime import date
from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.gipe import queries
from apps.gipe import service
from apps.gipe.tests.conftest import Bancos


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    cache.clear()


class TestJanela:
    def test_ano_letivo_vira_janela_de_ano_inteiro(self) -> None:
        assert service.janela_do_ano(2025) == {
            "inicio": date(2025, 1, 1),
            "fim": date(2026, 1, 1),
        }


class TestService:
    def test_sucesso_monta_contrato_e_cacheia(self, bancos: Bancos) -> None:
        contrato = service.obter_metricas(2026)

        assert contrato["atualizado_em"] is not None
        assert contrato["ano_letivo"] == 2026
        assert contrato["kpis"]["acesso_ativo"]["valor"] == 7
        assert contrato["ocorrencias"]["status_geral"]["cadastrados"] == 2
        assert contrato["usuarios"]["cadastrados"] == 11
        assert contrato["produtividade"]["atualizacoes_nas_ocorrencias"] == 4
        assert bancos.consultas("ocorrencias", queries.STATUS_GERAL) == [
            service.janela_do_ano(2026)
        ]
        # Movimentações alimentam dois blocos, mas são lidas uma vez só.
        assert len(bancos.consultas("ocorrencias", queries.MOVIMENTACOES)) == 1

        total_chamadas = len(bancos.chamadas)
        service.obter_metricas(2026)
        assert len(bancos.chamadas) == total_chamadas

    def test_anos_diferentes_nao_compartilham_cache(
        self, bancos: Bancos
    ) -> None:
        service.obter_metricas(2025)
        service.obter_metricas(2026)

        assert bancos.consultas("ocorrencias", queries.STATUS_GERAL) == [
            service.janela_do_ano(2025),
            service.janela_do_ano(2026),
        ]

    @pytest.mark.parametrize(
        "cliente",
        ["consultar_ocorrencias", "consultar_anexos", "consultar_usuarios"],
    )
    def test_falha_em_qualquer_banco_degrada_para_nulos(
        self, bancos: Bancos, cliente: str
    ) -> None:
        with patch(
            f"apps.gipe.client.{cliente}",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            contrato = service.obter_metricas(2026)

        assert contrato == {
            "atualizado_em": None,
            "ano_letivo": 2026,
            "kpis": None,
            "ocorrencias": None,
            "usuarios": None,
            "produtividade": None,
        }

    def test_falha_nao_e_cacheada(self, bancos: Bancos) -> None:
        with patch(
            "apps.gipe.client.consultar_ocorrencias",
            side_effect=psycopg.OperationalError("timeout"),
        ):
            service.obter_metricas(2026)

        assert service.obter_metricas(2026)["atualizado_em"] is not None
