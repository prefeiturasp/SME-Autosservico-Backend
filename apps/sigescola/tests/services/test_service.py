"""Testes da janela de datas, do cache e da degradação do serviço."""

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.sigescola import queries
from apps.sigescola import service

_HOJE = date(2026, 10, 9)

_PERIODOS = [
    {
        "referencia": "2026.3",
        "data_inicio": date(2026, 9, 2),
        "data_fim": None,
    },
    {
        "referencia": "2026.2",
        "data_inicio": date(2026, 5, 1),
        "data_fim": date(2026, 9, 1),
    },
]

# Ordem das consultas em obter_metricas sem DRE: períodos, usuários
# (cadastro e logins), PAA, prestação de contas (UEs aptas, status,
# créditos, despesas, demonstrativos e devolução) e bens.
_CONSULTAS_OK = [
    _PERIODOS,
    [{"total": 28, "novos_30_dias": 2}],
    [
        {
            "unicos_hoje": 2,
            "acessos_hoje": 2,
            "usuarios_dia_30_dias": 78,
            "acessos_30_dias": 127,
        }
    ],
    [
        {"situacao": "EM_ELABORACAO", "quantidade": 83},
        {"situacao": "GERADO", "quantidade": 35},
        {"situacao": "EM_RETIFICACAO", "quantidade": 46},
    ],
    [{"total": 1650}],
    [
        {"situacao": "EM_ANALISE", "quantidade": 2},
        {"situacao": "NAO_RECEBIDA", "quantidade": 2},
    ],
    [{"valor": Decimal("118502864.00")}],
    [{"valor": Decimal("578497.91")}],
    [{"total": 7}],
    [{"valor": Decimal("0")}],
    [{"quantidade": 7, "valor": Decimal("20199.90")}],
]


@pytest.fixture(autouse=True)
def _ambiente() -> Iterator[None]:
    """Cache vazio e "hoje" fixo a cada teste."""
    cache.clear()
    with patch(
        "apps.sigescola.service.timezone.localdate", return_value=_HOJE
    ):
        yield


class TestResolverJanela:
    """Cobre a conversão dos filtros em janela de datas."""

    def test_intervalo_vale_como_veio(self) -> None:
        """Com as duas datas, não há período e a janela é a informada."""
        janela = service.resolver_janela(
            _PERIODOS, None, date(2026, 1, 1), date(2026, 9, 22), _HOJE
        )

        assert janela == (None, date(2026, 1, 1), date(2026, 9, 22))

    def test_periodo_informado_usa_a_janela_dele(self) -> None:
        """Um período fechado usa as datas de despesa dele."""
        janela = service.resolver_janela(
            _PERIODOS, "2026.2", None, None, _HOJE
        )

        assert janela == ("2026.2", date(2026, 5, 1), date(2026, 9, 1))

    def test_sem_filtro_usa_o_corrente_ate_hoje(self) -> None:
        """Sem filtro, vale o período que contém hoje, terminando hoje."""
        janela = service.resolver_janela(_PERIODOS, None, None, None, _HOJE)

        assert janela == ("2026.3", date(2026, 9, 2), _HOJE)

    def test_sem_periodo_vigente_usa_o_mais_recente(self) -> None:
        """Se hoje cai fora de todos, usa o mais recente da lista."""
        janela = service.resolver_janela(
            _PERIODOS[1:], None, None, None, _HOJE
        )

        assert janela == ("2026.2", date(2026, 5, 1), date(2026, 9, 1))

    def test_periodo_inexistente(self) -> None:
        """Uma referência que não existe no PTRF levanta erro."""
        with pytest.raises(service.PeriodoNaoEncontradoError):
            service.resolver_janela(_PERIODOS, "1999.9", None, None, _HOJE)


class TestObterMetricas:
    """Cobre o contrato, o cache e a degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o contrato."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK)
            primeiro = service.obter_metricas()

        assert primeiro["atualizado_em"] is not None
        assert primeiro["filtros"] == {
            "periodo": "2026.3",
            "data_inicio": "2026-09-02",
            "data_fim": "2026-10-09",
            "dre": None,
            "ue": None,
        }
        assert primeiro["opcoes"] == {
            "periodos": ["2026.3", "2026.2"],
            "unidades": [],
        }
        assert primeiro["usuarios"]["com_acesso_ativo"]["valor"] == 28
        assert primeiro["plano_anual_de_atividades"] == {
            "em_andamento": 83,
            "finalizados": 35,
            "em_retificacao": 46,
        }
        assert primeiro["prestacao_de_contas"]["enviadas_ou_em_andamento"] == 2
        assert (
            primeiro["situacao_patrimonial"]["quantidade_bens_produzidos"] == 7
        )

        with patch("apps.sigescola.client.consultar") as consultar:
            service.obter_metricas()
            consultar.assert_not_called()

    def test_filtros_chegam_nas_consultas(self) -> None:
        """Intervalo e DRE viram o filtro das consultas e as opções de UE."""
        unidade = {"codigo_eol": "019715", "tipo_unidade": "EMEF", "nome": "X"}
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.side_effect = [_PERIODOS, [unidade], *_CONSULTAS_OK[1:]]
            contrato = service.obter_metricas(
                data_inicio=date(2026, 1, 1),
                data_fim=date(2026, 9, 22),
                dre="108100",
            )

        filtro = {
            "inicio": date(2026, 1, 1),
            "fim": date(2026, 9, 22),
            "dre": "108100",
            "ue": None,
        }
        consultar.assert_any_call(queries.UNIDADES_DA_DRE, {"dre": "108100"})
        consultar.assert_any_call(queries.PAA_POR_STATUS, filtro)
        consultar.assert_any_call(queries.BENS_PRODUZIDOS, filtro)
        assert contrato["filtros"]["periodo"] is None
        assert contrato["opcoes"]["unidades"] == [
            {"codigo_eol": "019715", "nome": "EMEF X"}
        ]

    def test_filtros_diferentes_nao_compartilham_cache(self) -> None:
        """A chave de cache separa as combinações de filtro."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK) * 2
            service.obter_metricas()
            service.obter_metricas(periodo="2026.2")

        assert consultar.call_count == 22

    def test_falha_de_banco_degrada_e_nao_cacheia(self) -> None:
        """Falha de conexão devolve blocos nulos e não fica no cache."""
        with patch(
            "apps.sigescola.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            resultado = service.obter_metricas(periodo="2026.2")

        assert resultado["atualizado_em"] is None
        assert resultado["filtros"]["periodo"] == "2026.2"
        assert resultado["opcoes"] is None
        assert resultado["prestacao_de_contas"] is None

        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.side_effect = list(_CONSULTAS_OK)
            service.obter_metricas(periodo="2026.2")

        assert consultar.call_count == 11

    def test_periodo_inexistente_propaga(self) -> None:
        """O erro de período chega à view (que devolve 400)."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.return_value = _PERIODOS
            with pytest.raises(service.PeriodoNaoEncontradoError):
                service.obter_metricas(periodo="1999.9")
