"""Testes de janelas, cache e degradação do serviço do Intranet."""

from datetime import datetime
from unittest.mock import patch

import pymysql
import pytest
from django.core.cache import cache

from apps.intranet import service


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    """Garante cache vazio a cada teste."""
    cache.clear()


# Ordem das consultas em obter_metricas: KPIs, Sorteios (status, tipo,
# ganhador, DRE), Ordem de Inscrição (idem) e Oportunidades.
_CONSULTAS_OK = [
    [{"com_acesso_ativo": 1, "unicos_hoje": 0}],
    [{"cadastrados": 30, "realizados": 15, "ativos": 0, "encerrados": 15}],
    [
        {"tipo_evento": "premio", "total": 13},
        {"tipo_evento": None, "total": 42},
    ],
    [{"ganhador": "servidor", "total": 39}],
    [{"dre": "DRE Penha", "total": 5}],
    [{"cadastrados": 6, "ativos": 0, "encerrados": 6}],
    [{"tipo_evento": "data", "total": 31}],
    [{"ganhador": "estagiario", "total": 4}],
    [{"dre": "DRE de teste", "total": 20}],
    [
        {
            "oportunidades_cadastradas": 2,
            "cvs_cadastrados": 3,
            "inscricoes_realizadas": 3,
            "contratacoes_efetivadas": 0,
        }
    ],
]

_AGORA = datetime(2026, 10, 7, 14, 30)


class TestJanelas:
    """Cobre a conversão de período/mês em janelas de datas."""

    @pytest.mark.parametrize(
        ("periodo", "inicio"),
        [
            ("geral", None),
            ("dia", datetime(2026, 10, 7)),
            ("quinzena", datetime(2026, 9, 22, 14, 30)),
            ("mes", datetime(2026, 9, 7, 14, 30)),
            ("trimestre", datetime(2026, 7, 9, 14, 30)),
        ],
    )
    def test_janela_movel_por_periodo(
        self, periodo: str, inicio: datetime | None
    ) -> None:
        """Cada período vira uma janela móvel até agora (sem fim)."""
        with patch.object(service, "_agora_local", return_value=_AGORA):
            janela = service._janela_periodo(periodo)

        assert janela == {"inicio": inicio, "fim": None}

    def test_janela_mes(self) -> None:
        """``AAAA-MM`` vira do dia 1 ao dia 1 do mês seguinte."""
        assert service._janela_mes("2026-09") == {
            "inicio": datetime(2026, 9, 1),
            "fim": datetime(2026, 10, 1),
        }

    def test_janela_mes_dezembro_vira_o_ano(self) -> None:
        """Dezembro termina em janeiro do ano seguinte."""
        assert service._janela_mes("2026-12")["fim"] == datetime(2027, 1, 1)

    def test_sem_mes_nao_filtra(self) -> None:
        """Sem mês, a janela não tem limites."""
        assert service._janela_mes(None) == {"inicio": None, "fim": None}

    def test_agora_local_sem_fuso(self) -> None:
        """WordPress grava hora local sem fuso; a janela também."""
        assert service._agora_local().tzinfo is None


class TestService:
    """Cobre cache e degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o resultado."""
        with patch("apps.intranet.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK)
            primeiro = service.obter_metricas()

        assert primeiro["atualizado_em"] is not None
        assert primeiro["periodo"] == "geral"
        assert primeiro["mes"] is None
        assert primeiro["kpis"]["acesso_ativo"]["valor"] == 1
        assert primeiro["sorteios"]["status_geral"]["cadastrados"] == 30
        assert primeiro["sorteios"]["por_tipo"][0] == {
            "label": "Não informado",
            "value": 42,
        }
        assert primeiro["ordem_inscricao"]["status_geral"]["encerrados"] == 6
        assert primeiro["oportunidades"]["cadastradas"] == 2

        with patch("apps.intranet.client.consultar") as consultar:
            service.obter_metricas()
            consultar.assert_not_called()

    def test_periodo_e_mes_separam_o_cache(self) -> None:
        """A chave de cache separa por período e por mês."""
        with patch("apps.intranet.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK) * 3
            service.obter_metricas("geral")
            service.obter_metricas("mes")
            service.obter_metricas("mes", "2026-09")

        assert consultar.call_count == 30

    def test_falha_de_banco_degrada_para_nulos(self) -> None:
        """Falha/timeout de conexão devolve o contrato com blocos nulos."""
        with patch(
            "apps.intranet.client.consultar",
            side_effect=pymysql.err.OperationalError(2003, "indisponivel"),
        ):
            resultado = service.obter_metricas("dia", "2026-09")

        assert resultado == {
            "atualizado_em": None,
            "periodo": "dia",
            "mes": "2026-09",
            "kpis": None,
            "sorteios": None,
            "ordem_inscricao": None,
            "oportunidades": None,
        }

    def test_falha_nao_e_cacheada(self) -> None:
        """Depois de uma falha, a próxima chamada tenta o banco de novo."""
        with patch(
            "apps.intranet.client.consultar",
            side_effect=pymysql.err.OperationalError(2013, "timeout"),
        ):
            service.obter_metricas()

        with patch("apps.intranet.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK)
            resultado = service.obter_metricas()

        assert resultado["atualizado_em"] is not None
