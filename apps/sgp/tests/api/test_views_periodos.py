"""Testes da view de períodos do SGP."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

_PERIODOS = {
    "periodos": [
        {
            "ano_letivo": 2026,
            "segmento": "eja",
            "semestre": 2,
            "bimestre": 1,
            "inicio": "2026-07-27",
            "fim": "2026-09-30",
        }
    ]
}


class TestPeriodosSgpView:
    """Testes cobrindo GET /api/v1/sgp/coped/periodos/."""

    def test_exige_api_key(self, api_client: APIClient) -> None:
        """Sem API Key, a view retorna 401."""
        response = api_client.get(reverse("sgp:periodos"))

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_retorna_periodos(self, api_client: APIClient, settings) -> None:
        """As opções do calendário são devolvidas como estão."""
        settings.API_KEY = "chave-correta"

        with patch("apps.sgp.service.obter_periodos", return_value=_PERIODOS):
            response = api_client.get(
                reverse("sgp:periodos"), HTTP_X_API_KEY="chave-correta"
            )

        assert response.status_code == http_status.HTTP_200_OK
        assert response.json() == _PERIODOS

    def test_preserva_periodos_nulos(
        self, api_client: APIClient, settings
    ) -> None:
        """Com o banco indisponível, ``periodos`` segue nulo."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sgp.service.obter_periodos",
            return_value={"periodos": None},
        ):
            response = api_client.get(
                reverse("sgp:periodos"), HTTP_X_API_KEY="chave-correta"
            )

        assert response.status_code == http_status.HTTP_200_OK
        assert response.json() == {"periodos": None}
