"""Testes da view de métricas do SGP."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.sgp.periodo import Periodo

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas do SGP."""
    return reverse("sgp:metricas")


_CONTRATO = {
    "atualizado_em": "2026-08-25T10:00:00-03:00",
    "ano_letivo": 2026,
    "bimestre": 2,
    "periodo": {
        "ano_letivo": 2026,
        "segmento": "fundamental_medio",
        "semestre": None,
        "bimestre": 2,
    },
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
        "esperado": 35179,
        "nao_iniciados": 8398,
        "processado_sucesso": 12398,
        "processado_pendencias": 7530,
        "processado_erro": 6853,
        "por_dre": [
            {
                "dre": "BT",
                "previsto": 3156,
                "nao_iniciados": 1736,
                "processado_sucesso": 980,
                "processado_pendencias": 240,
                "processado_erro": 200,
            }
        ],
    },
    "conselho_classe": {
        "esperado": 2480,
        "nao_iniciados": 204,
        "em_andamento": 387,
        "processado_sucesso": 1889,
        "por_dre": [
            {
                "dre": "BT",
                "previsto": 424,
                "nao_iniciados": 30,
                "em_andamento": 60,
                "processado_sucesso": 334,
            }
        ],
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
        obter.assert_called_once_with(Periodo(ano_letivo=2026, bimestre=2))
        corpo = response.json()
        assert corpo["fechamento"]["nao_iniciados"] == 8398
        assert corpo["fechamento"]["por_dre"][0]["dre"] == "BT"
        assert corpo["conselho_classe"]["esperado"] == 2480
        assert corpo["usuarios"]["com_acesso_ativo"]["valor"] == 8398
        assert corpo["frequencias"]["lancadas"] is None
        assert corpo["sondagens"]["esperadas"] is None

    def test_repassa_filtro_da_eja(
        self, api_client: APIClient, settings
    ) -> None:
        """Segmento e semestre da EJA chegam ao serviço."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sgp.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            response = api_client.get(
                _url(),
                {
                    "ano_letivo": "2026",
                    "bimestre": "1",
                    "segmento": "eja",
                    "semestre": "2",
                },
                HTTP_X_API_KEY="chave-correta",
            )

        assert response.status_code == http_status.HTTP_200_OK
        obter.assert_called_once_with(
            Periodo(ano_letivo=2026, bimestre=1, segmento="eja", semestre=2)
        )

    def test_semestre_e_ignorado_fora_da_eja(
        self, api_client: APIClient, settings
    ) -> None:
        """Em Fundamental/Médio, o semestre não entra no período."""
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.sgp.service.obter_metricas", return_value=_CONTRATO
        ) as obter:
            api_client.get(
                _url(),
                {"ano_letivo": 2026, "bimestre": 2, "semestre": 1},
                HTTP_X_API_KEY="chave-correta",
            )

        obter.assert_called_once_with(Periodo(ano_letivo=2026, bimestre=2))

    @pytest.mark.parametrize(
        ("params", "campo"),
        [
            ({"bimestre": 1, "segmento": "eja"}, "semestre"),
            ({"bimestre": 3, "segmento": "eja", "semestre": 1}, "bimestre"),
            ({"bimestre": 5}, "bimestre"),
            ({"bimestre": 1, "segmento": "infantil"}, "segmento"),
            ({"bimestre": "x"}, "bimestre"),
        ],
    )
    def test_filtros_invalidos(
        self,
        api_client: APIClient,
        settings,
        params: dict[str, str | int],
        campo: str,
    ) -> None:
        """Filtros fora das regras do segmento retornam 400."""
        settings.API_KEY = "chave-correta"

        with patch("apps.sgp.service.obter_metricas") as obter:
            response = api_client.get(
                _url(),
                {"ano_letivo": 2026, **params},
                HTTP_X_API_KEY="chave-correta",
            )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert campo in response.json()
        obter.assert_not_called()
