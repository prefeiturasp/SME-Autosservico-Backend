"""Testes do fluxo de métricas de provas do SERAp."""

from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.serap import handler
from apps.serap import mapper
from apps.serap import parser
from apps.serap import queries
from apps.serap import service


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    """Garante cache vazio a cada teste."""
    cache.clear()


_LINHA = [
    {
        "total": 100,
        "finalizadas": 80,
        "nao_finalizadas": 18,
        "iniciadas_hoje": 5,
    }
]


class TestParser:
    """Cobre a interpretação da linha do agregado."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, todos os contadores voltam zerados."""
        assert parser.parse_provas([]) == {
            "total": 0,
            "finalizadas": 0,
            "nao_finalizadas": 0,
            "iniciadas_hoje": 0,
        }


class TestMapper:
    """Cobre a montagem do bloco de provas."""

    def test_percentual_finalizadas(self) -> None:
        """O percentual é finalizadas/total em pontos percentuais."""
        bloco = mapper.mapear_provas(
            {
                "total": 100,
                "finalizadas": 80,
                "nao_finalizadas": 18,
                "iniciadas_hoje": 5,
            }
        )

        assert bloco["percentual_finalizadas"] == 80.0
        assert bloco["finalizadas"] == 80
        assert bloco["iniciadas_hoje"] == 5

    def test_total_zero_nao_divide_por_zero(self) -> None:
        """Sem provas, o percentual é zero (sem divisão por zero)."""
        bloco = mapper.mapear_provas(
            {
                "total": 0,
                "finalizadas": 0,
                "nao_finalizadas": 0,
                "iniciadas_hoje": 0,
            }
        )

        assert bloco["percentual_finalizadas"] == 0.0


class TestHandler:
    """Cobre a escolha da query conforme a janela."""

    def test_sem_janela_usa_agregado_global(self) -> None:
        """Sem janela, consulta o agregado global (sem parâmetros)."""
        with patch("apps.serap.client.consultar") as consultar:
            consultar.return_value = _LINHA
            handler.obter_provas(None)

        consultar.assert_called_once_with(queries.PROVAS_AGREGADO)

    def test_com_janela_recorta_por_datas(self) -> None:
        """Com janela, consulta o agregado recortado por datas."""
        janela = ("2026-05-01", "2026-07-11")
        with patch("apps.serap.client.consultar") as consultar:
            consultar.return_value = _LINHA
            handler.obter_provas(janela)

        consultar.assert_called_once_with(
            queries.PROVAS_AGREGADO_JANELA, janela
        )


class TestService:
    """Cobre cache e degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o resultado."""
        with patch("apps.serap.client.consultar") as consultar:
            consultar.return_value = _LINHA
            primeiro = service.obter_provas(2026, 2)

        assert primeiro["atualizado_em"] is not None
        assert primeiro["ano"] == 2026
        assert primeiro["provas"]["total"] == 100
        assert primeiro["provas"]["percentual_finalizadas"] == 80.0

        with patch("apps.serap.client.consultar") as consultar:
            service.obter_provas(2026, 2)
            consultar.assert_not_called()

    def test_falha_de_banco_degrada_para_nulo(self) -> None:
        """Falha de conexão devolve o contrato com o bloco nulo."""
        with patch(
            "apps.serap.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            resultado = service.obter_provas(2026, 2)

        assert resultado["atualizado_em"] is None
        assert resultado["ano"] == 2026
        assert resultado["provas"] is None
