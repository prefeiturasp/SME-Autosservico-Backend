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
        "com_acesso_ativo": {
            "total": 10,
            "ativos_30_dias": 4,
            "novos_30_dias": 2,
        },
        "unicos_por_dia": None,
        "acessos_hoje": None,
        "por_tipo_perfil": {"codae": 3, "dre": 0, "ue": 0, "empresa": 0},
        "comparativo_acessos": None,
    },
    "alimentacao_terceirizada": {
        "medicoes_iniciais": {
            "aguardando_envio_ue": None,
            "enviadas_pelas_unidades": None,
            "aprovadas_pelas_dres": None,
            "aguardando_codae": None,
            "aprovadas_codae": None,
        },
        "produtos_homologados": {
            "total_cadastrados": 6,
            "homologados": 0,
            "solicitacoes_no_mes": 0,
            "solicitacoes_no_ano": 0,
        },
        "empresas_terceirizadas": {"cadastradas": 7, "ativas": 5},
        "solicitacoes_dietas_especiais": {
            "dia": {
                "total": 0,
                "autorizadas": 0,
                "aguardando": 0,
                "negadas": 0,
                "canceladas": 0,
            },
            "quinzena": {
                "total": 5,
                "autorizadas": 2,
                "aguardando": 3,
                "negadas": 0,
                "canceladas": 0,
            },
            "mes": {
                "total": 5,
                "autorizadas": 2,
                "aguardando": 3,
                "negadas": 0,
                "canceladas": 0,
            },
            "trimestre": {
                "total": 5,
                "autorizadas": 2,
                "aguardando": 3,
                "negadas": 0,
                "canceladas": 0,
            },
        },
        "solicitacoes_alimentacoes": {
            "dia": {
                "total": 0,
                "autorizadas": 0,
                "aguardando": 0,
                "negadas": 0,
                "canceladas": 0,
            },
            "quinzena": {
                "total": 19,
                "autorizadas": 10,
                "aguardando": 0,
                "negadas": 9,
                "canceladas": 0,
            },
            "mes": {
                "total": 19,
                "autorizadas": 10,
                "aguardando": 0,
                "negadas": 9,
                "canceladas": 0,
            },
            "trimestre": {
                "total": 19,
                "autorizadas": 10,
                "aguardando": 0,
                "negadas": 9,
                "canceladas": 0,
            },
        },
    },
    "logistica": {
        "cronogramas_entregas": {
            "aguardando": 2,
            "enviadas": 3,
            "aprovadas": 1,
        },
        "fichas_tecnicas_produtos": {
            "cadastradas": 10,
            "aprovadas": 6,
            "em_analise": 3,
            "pendentes_correcao": 1,
        },
        "fornecedores_distribuidores": {"cadastradas": 8, "ativas": 5},
        "layouts_embalagens": {
            "cadastrados": 7,
            "aprovados": 4,
            "aguardando_codae": 2,
            "pendentes_correcao": 1,
        },
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
            "novos_30_dias": 2,
        }
        assert corpo["usuarios"]["unicos_por_dia"] is None
        assert corpo["usuarios"]["por_tipo_perfil"]["codae"] == 3
