"""Testes da view de métricas de provas do SERAp."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas de provas do SERAp."""
    return reverse("serap:provas-metricas")


_CONTRATO = {
    "atualizado_em": "2026-08-25T10:00:00-03:00",
    "ano": 2026,
    "bimestre": 2,
    "provas": {
        "total": 8398,
        "iniciadas_hoje": 7530,
        "nao_finalizadas": 1853,
        "finalizadas": 6398,
        "percentual_finalizadas": 76.2,
    },
}


class TestMetricasProvasSerapView:
    """Testes cobrindo GET /api/v1/serap/provas/metricas/."""

    def test_exige_api_key(self, api_client: APIClient) -> None:
        """Sem API Key, a view retorna 401."""
        response = api_client.get(_url(), {"ano": 2026, "bimestre": 2})

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_parametros_obrigatorios(
        self, api_client: APIClient, settings
    ) -> None:
        """Sem ano/bimestre, a view retorna 400."""
        settings.API_KEY = "chave-correta"

        response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "ano" in response.json()

    def test_parametro_nao_inteiro(
        self, api_client: APIClient, settings
    ) -> None:
        """Parâmetro não inteiro retorna 400."""
        settings.API_KEY = "chave-correta"

        response = api_client.get(
            _url(),
            {"ano": "abc", "bimestre": 2},
            HTTP_X_API_KEY="chave-correta",
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "ano" in response.json()

    def test_retorna_contrato(self, api_client: APIClient, settings) -> None:
        """O contrato de provas é serializado corretamente."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.serap.service.obter_provas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(
                _url(),
                {"ano": 2026, "bimestre": 2},
                HTTP_X_API_KEY="chave-correta",
            )

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with(2026, 2)
        corpo = response.json()
        assert corpo["provas"]["total"] == 8398
        assert corpo["provas"]["percentual_finalizadas"] == pytest.approx(76.2)
