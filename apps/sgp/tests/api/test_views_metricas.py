"""Testes da view de métricas do SGP."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas do SGP."""
    return reverse("sgp:metricas")


_CONTRATO = {
    "atualizado_em": "2026-08-25T10:00:00-03:00",
    "ano_letivo": 2026,
    "bimestre": 2,
    "usuarios": {
        "com_acesso_ativo": {"valor": 8398, "variacao_30_dias": 453},
        "de_unidades_educacionais": {
            "total": 200,
            "diretorias_regionais": 13,
        },
        "unicos_por_dia": None,
        "acessos_por_hora": None,
    },
    "frequencias": {"lancadas": None, "esperadas": None, "percentual": None},
    "sondagens": {"realizadas": None, "esperadas": None},
    "fechamento": {
        "nao_iniciados": 8398,
        "processado_sucesso": 7530,
        "processado_pendencias": 6853,
        "processado_erro": 12398,
    },
    "conselho_classe": {
        "nao_iniciados": 204,
        "em_andamento": 387,
        "processado_sucesso": 1889,
    },
}


class TestMetricasSgpView:
    """Testes cobrindo GET /api/v1/sgp/coped/metricas/."""

    def test_exige_api_key(self, api_client: APIClient) -> None:
        """Sem API Key, a view retorna 401."""
        response = api_client.get(_url(), {"ano_letivo": 2026, "bimestre": 2})

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_parametros_obrigatorios(
        self, api_client: APIClient, settings
    ) -> None:
        """Sem ano_letivo/bimestre, a view retorna 400."""
        settings.API_KEY = "chave-correta"

        response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "ano_letivo" in response.json()

    def test_retorna_contrato_com_gaps_nulos(
        self, api_client: APIClient, settings
    ) -> None:
        """O contrato é serializado preservando os indicadores nulos."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sgp.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(
                _url(),
                {"ano_letivo": 2026, "bimestre": 2},
                HTTP_X_API_KEY="chave-correta",
            )

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with(2026, 2)
        corpo = response.json()
        assert corpo["fechamento"]["nao_iniciados"] == 8398
        assert corpo["usuarios"]["com_acesso_ativo"]["valor"] == 8398
        assert corpo["frequencias"]["lancadas"] is None
        assert corpo["sondagens"]["esperadas"] is None
