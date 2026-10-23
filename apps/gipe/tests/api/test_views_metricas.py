"""Testes da view de métricas do GIPE."""

from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.gipe.tests.conftest import Bancos

pytestmark = pytest.mark.django_db

_CHAVE = "chave-correta"


@pytest.fixture(autouse=True)
def _api_key(settings) -> None:
    settings.API_KEY = _CHAVE
    cache.clear()


def _get(api_client: APIClient, params: dict | None = None, **headers):
    return api_client.get(reverse("gipe:metricas"), params or {}, **headers)


class TestMetricasGipeView:
    def test_exige_api_key(self, api_client: APIClient) -> None:
        response = _get(api_client, {"ano_letivo": "2026"})

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "params", [{}, {"ano_letivo": "abc"}, {"ano_letivo": "1999"}]
    )
    def test_ano_letivo_obrigatorio_e_valido(
        self, api_client: APIClient, params: dict
    ) -> None:
        response = _get(api_client, params, HTTP_X_API_KEY=_CHAVE)

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert "ano_letivo" in response.json()

    def test_retorna_contrato_completo(
        self, api_client: APIClient, bancos: Bancos
    ) -> None:
        response = _get(
            api_client, {"ano_letivo": "2026"}, HTTP_X_API_KEY=_CHAVE
        )

        assert response.status_code == http_status.HTTP_200_OK
        corpo = response.json()
        assert corpo["ano_letivo"] == 2026
        assert corpo["kpis"]["acesso_ativo"]["tendencia"] == "above"
        assert corpo["ocorrencias"]["por_dre"] == [
            {"label": "Ipiranga", "value": 2}
        ]
        assert corpo["ocorrencias"]["por_mes"][0]["pico"] is True
        assert corpo["usuarios"]["por_tipo_de_perfil"][0]["percentage"] == 45
        assert corpo["produtividade"]["anexos_enviados"] == 0

    def test_contrato_degradado_preserva_nulos(
        self, api_client: APIClient
    ) -> None:
        indisponivel = {
            "atualizado_em": None,
            "ano_letivo": 2026,
            "kpis": None,
            "ocorrencias": None,
            "usuarios": None,
            "produtividade": None,
        }
        with patch(
            "apps.gipe.service.obter_metricas", return_value=indisponivel
        ) as obter:
            response = _get(
                api_client, {"ano_letivo": "2026"}, HTTP_X_API_KEY=_CHAVE
            )

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with(2026)
        assert response.json() == indisponivel
