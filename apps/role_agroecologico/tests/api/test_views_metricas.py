"""Testes da view de métricas do Rolê Agroecológico."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _url() -> str:
    """Monta a URL da view de métricas do Rolê Agroecológico."""
    return reverse("role_agroecologico:metricas")


_CONTRATO = {
    "atualizado_em": "2026-11-10T10:00:00-03:00",
    "indicadores_participacao_logistica": {
        "vivencias_realizadas": 2,
        "estudantes_participantes": 3,
        "estudantes_inscritos": 6,
        "participantes_vivencias": 5,
        "educadores_participantes": 1,
        "refeicoes_estudantes": 2,
        "kits_distribuidos": None,
        "vivencias_com_refeicao": {
            "valor": 1,
            "total_realizadas": 2,
            "progresso_percentual": 50.0,
        },
        "ues_participantes_por_dre": [{"label": "DRE Butantã", "value": 1}],
    },
    "unidades_produtivas": {
        "ups_cadastradas": 3,
        "ups_preservacao_ambiental_manancial": 2,
        "ups_que_receberam_visita": 1,
        "lista_ups_que_receberam_visita": ["Fazenda Vale"],
        "perfil_responsaveis_ups": None,
    },
    "agendamentos_roles": {
        "agendamentos_totais": 4,
        "agendamentos_ultima_semana": 1,
        "roles_concluidos": 2,
        "roles_previstos_semana": 1,
        "agendamentos_por_dre": [{"label": "Não informado", "value": 4}],
    },
}

_INDISPONIVEL = {
    "atualizado_em": None,
    "indicadores_participacao_logistica": None,
    "unidades_produtivas": None,
    "agendamentos_roles": None,
}


class TestMetricasRoleAgroecologicoView:
    def test_exige_api_key(self, api_client: APIClient) -> None:
        response = api_client.get(_url())

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_entrega_o_contrato(self, api_client: APIClient, settings) -> None:
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.role_agroecologico.service.obter_metricas",
            return_value=_CONTRATO,
        ):
            response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_200_OK
        assert response.json() == _CONTRATO

    def test_contrato_degradado_preserva_nulos(
        self, api_client: APIClient, settings
    ) -> None:
        settings.API_KEY = "chave-correta"

        with patch(
            "apps.role_agroecologico.service.obter_metricas",
            return_value=_INDISPONIVEL,
        ):
            response = api_client.get(_url(), HTTP_X_API_KEY="chave-correta")

        assert response.status_code == http_status.HTTP_200_OK
        assert response.json() == _INDISPONIVEL
