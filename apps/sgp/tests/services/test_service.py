"""Testes de cache e degradação do serviço de métricas do SGP."""

from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.sgp import service


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    """Garante cache vazio a cada teste."""
    cache.clear()


# Ordem das consultas em obter_metricas: acesso ativo, unidades,
# fechamento, conselho (situação), conselho (alunos ativos).
_CONSULTAS_OK = [
    [{"total": 8398, "ativos_30_dias": 453}],
    [{"total": 200, "diretorias": 13}],
    [{"situacao": 3, "quantidade": 7530}],
    [{"situacao": 1, "quantidade": 387}],
    [{"alunos_ativos": 591}],
]


class TestService:
    """Cobre cache e degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o resultado."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK)
            primeiro = service.obter_metricas(2026, 2)

        assert primeiro["atualizado_em"] is not None
        assert primeiro["ano_letivo"] == 2026
        assert primeiro["usuarios"]["com_acesso_ativo"]["valor"] == 8398
        assert primeiro["fechamento"]["processado_sucesso"] == 7530
        assert primeiro["conselho_classe"]["nao_iniciados"] == 204
        assert primeiro["frequencias"]["lancadas"] is None

        with patch("apps.sgp.client.consultar") as consultar:
            service.obter_metricas(2026, 2)
            consultar.assert_not_called()

    def test_periodos_diferentes_nao_compartilham_cache(self) -> None:
        """A chave de cache separa por ano letivo e bimestre."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK) + list(_CONSULTAS_OK)
            service.obter_metricas(2026, 2)
            service.obter_metricas(2026, 3)

        assert consultar.call_count == 10

    def test_falha_de_banco_degrada_para_nulos(self) -> None:
        """Falha de conexão devolve o contrato com blocos nulos."""
        with patch(
            "apps.sgp.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            resultado = service.obter_metricas(2026, 2)

        assert resultado["atualizado_em"] is None
        assert resultado["ano_letivo"] == 2026
        assert resultado["usuarios"] is None
        assert resultado["fechamento"] is None
        assert resultado["conselho_classe"] is None
