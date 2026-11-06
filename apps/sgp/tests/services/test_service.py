"""Testes de cache e degradação do serviço de métricas do SGP."""

from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.sgp import service
from apps.sgp.periodo import SEGMENTO_EJA
from apps.sgp.periodo import Periodo


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    """Garante cache vazio a cada teste."""
    cache.clear()


_PERIODO = Periodo(ano_letivo=2026, bimestre=2)

# Na ordem em que obter_metricas consulta o banco.
_CONSULTAS_OK = [
    [{"total": 8398, "ativos_30_dias": 453}],
    [{"total": 200, "diretorias": 13}],
    [{"esperadas": 21760, "lancadas": 18432}],
    [{"esperadas": 2683, "realizadas": 1243}],
    [{"dre": "BT", "situacao": 3, "quantidade": 7530}],
    [{"dre": "BT", "situacao": 1, "quantidade": 387}],
    [{"dre": "BT", "previsto": 591}],
]


class TestService:
    """Cobre cache e degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o resultado."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK)
            primeiro = service.obter_metricas(_PERIODO)

        assert primeiro["atualizado_em"] is not None
        assert primeiro["ano_letivo"] == 2026
        assert primeiro["periodo"] == {
            "ano_letivo": 2026,
            "segmento": "fundamental_medio",
            "semestre": None,
            "bimestre": 2,
        }
        assert primeiro["usuarios"]["com_acesso_ativo"]["valor"] == 8398
        assert primeiro["fechamento"]["processado_sucesso"] == 7530
        assert primeiro["fechamento"]["esperado"] == 7530
        assert primeiro["conselho_classe"]["nao_iniciados"] == 204
        assert primeiro["sondagens"] == {"realizadas": 1243, "esperadas": 2683}
        assert primeiro["frequencias"]["lancadas"] == 18432
        assert primeiro["frequencias"]["esperadas"] == 21760

        with patch("apps.sgp.client.consultar") as consultar:
            service.obter_metricas(_PERIODO)
            consultar.assert_not_called()

    @pytest.mark.parametrize(
        "outro",
        [
            Periodo(ano_letivo=2026, bimestre=3),
            Periodo(
                ano_letivo=2026, bimestre=2, segmento=SEGMENTO_EJA, semestre=1
            ),
        ],
    )
    def test_periodos_diferentes_nao_compartilham_cache(self, outro) -> None:
        """A chave de cache separa por bimestre, segmento e semestre."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK) + list(_CONSULTAS_OK)
            service.obter_metricas(_PERIODO)
            service.obter_metricas(outro)

        assert consultar.call_count == 14

    def test_falha_de_banco_degrada_para_nulos(self) -> None:
        """Falha de conexão devolve o contrato com blocos nulos."""
        with patch(
            "apps.sgp.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            resultado = service.obter_metricas(_PERIODO)

        assert resultado["atualizado_em"] is None
        assert resultado["ano_letivo"] == 2026
        assert resultado["periodo"]["segmento"] == "fundamental_medio"
        assert resultado["usuarios"] is None
        assert resultado["fechamento"] is None
        assert resultado["conselho_classe"] is None


class TestPeriodos:
    """Cobre cache e degradação das opções de período."""

    def test_consulta_so_o_ano_corrente_e_cacheia(self) -> None:
        """Busca só o ano corrente; a segunda chamada é cache."""
        with (
            patch("apps.sgp.client.consultar", return_value=[]) as consultar,
            patch(
                "apps.sgp.service.timezone.localdate",
            ) as localdate,
        ):
            localdate.return_value.year = 2026
            assert service.obter_periodos() == {"periodos": []}
            service.obter_periodos()

        consultar.assert_called_once()
        assert consultar.call_args.args[1] == {
            "ano_inicial": 2026,
            "ano_final": 2026,
        }

    def test_falha_de_banco_devolve_nulo_sem_cachear(self) -> None:
        """Em falha, ``periodos`` é nulo e a próxima chamada tenta de novo."""
        with patch(
            "apps.sgp.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ) as consultar:
            assert service.obter_periodos() == {"periodos": None}
            service.obter_periodos()

        assert consultar.call_count == 2
