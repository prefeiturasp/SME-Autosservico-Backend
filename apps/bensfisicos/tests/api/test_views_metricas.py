"""Testes da view de métricas do Bens Físicos."""

from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.bensfisicos.tests.services.test_service import DEGRADADO

pytestmark = pytest.mark.django_db

_CHAVE = "chave-correta"


@pytest.fixture(autouse=True)
def _api_key(settings) -> None:
    settings.API_KEY = _CHAVE
    cache.clear()


def _get(api_client: APIClient, **headers):
    return api_client.get(reverse("bensfisicos:metricas"), **headers)


class TestMetricasBensFisicosView:
    def test_exige_api_key(self, api_client: APIClient) -> None:
        response = _get(api_client)

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_retorna_contrato_completo(
        self, api_client: APIClient, banco: list[str]
    ) -> None:
        response = _get(api_client, HTTP_X_API_KEY=_CHAVE)

        assert response.status_code == http_status.HTTP_200_OK
        corpo = response.json()
        assert corpo["usuarios"]["unicos_por_dia"] == {
            "valor": 1,
            "variacao_percentual_30_dias": 233.3,
        }
        assert corpo["cadastro_de_bens"]["por_unidade_administrativa"] == [
            {
                "sigla": "SMECOTIC",
                "nome": "COORDENADORIA DE TECNOLOGIA",
                "bens": 493,
            },
            {"sigla": "SPDM", "nome": "SPDM", "bens": 339},
        ]
        assert corpo["baixas_fisicas"]["aprovadas"] == 42
        assert corpo["movimentacoes"]["transferencias_realizadas"] == 7

    def test_contrato_degradado_preserva_nulos(
        self, api_client: APIClient
    ) -> None:
        with patch(
            "apps.bensfisicos.service.obter_metricas", return_value=DEGRADADO
        ):
            response = _get(api_client, HTTP_X_API_KEY=_CHAVE)

        assert response.status_code == http_status.HTTP_200_OK
        assert response.json() == DEGRADADO
