"""Testes da view de métricas do SIGPAE."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas do SIGPAE."""
    return reverse("sigpae:metricas")


_CONTRATO = {
    "atualizado_em": "2026-08-25T10:00:00-03:00",
    "usuarios": {
        "com_acesso_ativo": {"total": 10, "ativos_30_dias": 4},
        "unicos_por_dia": None,
        "acessos_hoje": None,
        "por_tipo_perfil": {"codae": 3, "dre": 0, "ue": 0, "empresa": 0},
        "comparativo_acessos": None,
    },
}


class TestMetricasSigpaeView:
    """Testes cobrindo GET /api/v1/sigpae/metricas/."""

    def test_exige_api_key(self, api_client: APIClient) -> None:
        """Sem API Key, a view retorna 401."""
        response = api_client.get(_url())

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_retorna_contrato_com_gaps_nulos(
        self, api_client: APIClient, settings
    ) -> None:
        """O contrato é serializado preservando os indicadores nulos."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sigpae.service.obter_metricas", return_value=_CONTRATO
        ):
            response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_200_OK
        corpo = response.json()
        assert corpo["usuarios"]["com_acesso_ativo"] == {
            "total": 10,
            "ativos_30_dias": 4,
        }
        assert corpo["usuarios"]["unicos_por_dia"] is None
        assert corpo["usuarios"]["por_tipo_perfil"]["codae"] == 3
