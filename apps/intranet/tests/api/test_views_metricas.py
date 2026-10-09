"""Testes da view de métricas do Intranet."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas do Intranet."""
    return reverse("intranet:metricas")


def _kpi(valor: int) -> dict:
    """KPI no formato do contrato, sem tendência."""
    return {"valor": valor, "tendencia": None, "tendencia_label": None}


_CONTRATO = {
    "atualizado_em": "2026-09-24T10:00:00-03:00",
    "periodo": "geral",
    "mes": None,
    "kpis": {
        "acesso_ativo": _kpi(1),
        "usuarios_unicos": _kpi(0),
        "acessos_hoje": _kpi(0),
    },
    "sorteios": {
        "status_geral": {
            "cadastrados": 30,
            "realizados": 15,
            "ativos": 0,
            "encerrados": 15,
        },
        "por_tipo": [{"label": "Premiação", "value": 13}],
        "por_ganhador": [{"label": "Servidores", "value": 39}],
        "por_dre": [{"label": "DRE Santo Amaro", "value": 9}],
    },
    "ordem_inscricao": {
        "status_geral": {"cadastrados": 6, "ativos": 0, "encerrados": 6},
        "por_tipo": [{"label": "Data específica", "value": 31}],
        "por_ganhador": [{"label": "Servidores", "value": 31}],
        "por_dre": [{"label": "DRE de teste", "value": 20}],
    },
    "oportunidades": {
        "cadastradas": 2,
        "cvs_cadastrados": 3,
        "inscricoes_realizadas": 3,
        "contratacoes_efetivadas": 0,
    },
}

_INDISPONIVEL = {
    "atualizado_em": None,
    "periodo": "geral",
    "mes": None,
    "kpis": None,
    "sorteios": None,
    "ordem_inscricao": None,
    "oportunidades": None,
}


class TestMetricasIntranetView:
    """Testes cobrindo GET /api/v1/intranet/metricas/."""

    def test_exige_api_key(self, api_client: APIClient) -> None:
        """Sem API Key, a view retorna 401."""
        response = api_client.get(_url())

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_sem_parametros_usa_geral(
        self, api_client: APIClient, settings
    ) -> None:
        """Sem parâmetros, o serviço recebe ``geral`` e mês nulo."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.intranet.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with("geral", None)
        corpo = response.json()
        assert corpo["sorteios"]["status_geral"]["realizados"] == 15
        assert corpo["kpis"]["acessos_hoje"]["tendencia"] is None
        assert corpo["oportunidades"]["cadastradas"] == 2

    def test_repassa_periodo_e_mes(
        self, api_client: APIClient, settings
    ) -> None:
        """``periodo`` e ``mes`` válidos chegam ao serviço."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.intranet.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(
                _url(),
                {"periodo": "trimestre", "mes": "2026-09"},
                HTTP_X_API_KEY="chave-correta",
            )

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with("trimestre", "2026-09")

    @pytest.mark.parametrize("periodo", ["semana", "MES", "1"])
    def test_periodo_invalido(
        self, api_client: APIClient, settings, periodo: str
    ) -> None:
        """Período fora da lista retorna 400."""
        settings.API_KEY = "chave-correta"

        response = api_client.get(
            _url(), {"periodo": periodo}, HTTP_X_API_KEY="chave-correta"
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "periodo" in response.json()

    @pytest.mark.parametrize("mes", ["2026-13", "2026-9", "09-2026", "abc"])
    def test_mes_invalido(
        self, api_client: APIClient, settings, mes: str
    ) -> None:
        """Mês fora do formato AAAA-MM retorna 400."""
        settings.API_KEY = "chave-correta"

        response = api_client.get(
            _url(), {"mes": mes}, HTTP_X_API_KEY="chave-correta"
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "mes" in response.json()

    def test_contrato_degradado_preserva_nulos(
        self, api_client: APIClient, settings
    ) -> None:
        """Com o banco indisponível, os blocos nulos chegam ao BFF."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.intranet.service.obter_metricas",
            return_value=_INDISPONIVEL,
        ):
            response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_200_OK
        assert response.json() == _INDISPONIVEL
