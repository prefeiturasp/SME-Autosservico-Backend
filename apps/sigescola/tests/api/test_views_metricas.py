"""Testes da view de métricas do SIG-Escola."""

from datetime import date
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.sigescola import service

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas do SIG-Escola."""
    return reverse("sigescola:metricas")


_CONTRATO = {
    "atualizado_em": "2026-10-09T10:00:00-03:00",
    "filtros": {
        "periodo": "2026.3",
        "data_inicio": "2026-09-02",
        "data_fim": "2026-10-09",
        "dre": None,
        "ue": None,
    },
    "opcoes": {"periodos": ["2026.3", "2026.2"], "unidades": []},
    "usuarios": {
        "com_acesso_ativo": {"valor": 28, "variacao_30_dias": 2},
        "unicos_por_dia": {"valor": 2, "variacao_percentual_30_dias": -23.1},
        "acessos_hoje": {"valor": 2, "variacao_percentual_30_dias": -52.8},
    },
    "plano_anual_de_atividades": {
        "em_andamento": 83,
        "finalizados": 35,
        "em_retificacao": 46,
    },
    "prestacao_de_contas": {
        "ues_aptas": 1650,
        "enviadas_ou_em_andamento": 0,
        "creditos_disponiveis": 0.0,
        "despesas_registradas": 5300.0,
        "demonstrativos_gerados": 0,
        "devolucao_ao_tesouro": 0.0,
    },
    "situacao_patrimonial": {
        "quantidade_bens_produzidos": 2,
        "valor_bens_produzidos": 200.0,
    },
}


class TestMetricasSigEscolaView:
    """Testes cobrindo GET /api/v1/sigescola/metricas/."""

    def test_exige_api_key(self, api_client: APIClient) -> None:
        """Sem API Key, a view retorna 401."""
        response = api_client.get(_url())

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_sem_filtros_usa_o_padrao(
        self, api_client: APIClient, settings
    ) -> None:
        """Sem filtros, o serviço recebe tudo None e o contrato volta."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sigescola.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with(
            periodo=None, data_inicio=None, data_fim=None, dre=None, ue=None
        )
        corpo = response.json()
        assert corpo["plano_anual_de_atividades"]["em_andamento"] == 83
        assert corpo["opcoes"]["periodos"] == ["2026.3", "2026.2"]
        assert corpo["usuarios"]["com_acesso_ativo"]["variacao_30_dias"] == 2
        assert corpo["usuarios"]["unicos_por_dia"]["valor"] == 2

    def test_intervalo_e_dre_viram_datas(
        self, api_client: APIClient, settings
    ) -> None:
        """As datas chegam ao serviço como ``date``."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sigescola.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(
                _url(),
                {
                    "data_inicio": "2026-01-01",
                    "data_fim": "2026-09-22",
                    "dre": "108100",
                },
                HTTP_X_API_KEY="chave-correta",
            )

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with(
            periodo=None,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 9, 22),
            dre="108100",
            ue=None,
        )

    @pytest.mark.parametrize(
        "params",
        [
            {
                "periodo": "2026.2",
                "data_inicio": "2026-01-01",
                "data_fim": "2026-09-22",
            },
            {"data_inicio": "2026-01-01"},
            {"data_inicio": "2026-09-22", "data_fim": "2026-01-01"},
            {"dre": "butanta"},
            {"periodo": "2026-2"},
        ],
    )
    def test_filtros_invalidos(
        self, api_client: APIClient, settings, params: dict[str, str]
    ) -> None:
        """Combinações ou formatos inválidos retornam 400."""
        settings.API_KEY = "chave-correta"

        response = api_client.get(
            _url(), params, HTTP_X_API_KEY="chave-correta"
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_periodo_inexistente(
        self, api_client: APIClient, settings
    ) -> None:
        """Período que não existe no PTRF retorna 400."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sigescola.service.obter_metricas",
            side_effect=service.PeriodoNaoEncontradoError("1999.9"),
        ):
            response = api_client.get(
                _url(), {"periodo": "1999.9"}, HTTP_X_API_KEY="chave-correta"
            )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "periodo" in response.json()
