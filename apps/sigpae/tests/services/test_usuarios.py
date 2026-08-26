"""Testes do fluxo de métricas de usuários do SIGPAE."""

from unittest.mock import patch

import psycopg
import pytest
from django.core.cache import cache

from apps.sigpae import handler
from apps.sigpae import mapper
from apps.sigpae import parser
from apps.sigpae import service


@pytest.fixture(autouse=True)
def _limpar_cache() -> None:
    """Garante cache vazio a cada teste."""
    cache.clear()


class TestParser:
    """Cobre a interpretação das linhas cruas do banco."""

    def test_acesso_ativo_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, os contadores voltam zerados."""
        assert parser.parse_acesso_ativo([]) == {
            "total": 0,
            "ativos_30_dias": 0,
        }

    def test_por_tipo_perfil_normaliza_visao(self) -> None:
        """A visão é normalizada para maiúsculas."""
        linhas = [
            {"visao": "codae", "total_usuarios": 3},
            {"visao": "UE", "total_usuarios": 5},
        ]

        assert parser.parse_por_tipo_perfil(linhas) == {"CODAE": 3, "UE": 5}


class TestMapper:
    """Cobre a montagem do bloco de contrato."""

    def test_gaps_viram_null_e_perfis_completam_zero(self) -> None:
        """Indicadores sem fonte são None; perfis ausentes viram zero."""
        bloco = mapper.mapear_usuarios(
            {"total": 10, "ativos_30_dias": 4}, {"CODAE": 3}
        )

        assert bloco["com_acesso_ativo"] == {
            "total": 10,
            "ativos_30_dias": 4,
        }
        assert bloco["unicos_por_dia"] is None
        assert bloco["acessos_hoje"] is None
        assert bloco["comparativo_acessos"] is None
        assert bloco["por_tipo_perfil"] == {
            "codae": 3,
            "dre": 0,
            "ue": 0,
            "empresa": 0,
        }


class TestHandler:
    """Cobre a orquestração das consultas."""

    def test_orquestra_queries_parser_e_mapper(self) -> None:
        """O handler compõe as duas consultas no bloco final."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 10, "ativos_30_dias": 4}],
                [{"visao": "CODAE", "total_usuarios": 3}],
            ]
            bloco = handler.obter_usuarios()

        assert bloco["com_acesso_ativo"]["total"] == 10
        assert bloco["por_tipo_perfil"]["codae"] == 3


class TestService:
    """Cobre cache e degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o resultado."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 10, "ativos_30_dias": 4}],
                [{"visao": "CODAE", "total_usuarios": 3}],
            ]
            primeiro = service.obter_metricas()

        assert primeiro["atualizado_em"] is not None
        assert primeiro["usuarios"]["com_acesso_ativo"]["total"] == 10
        medicoes = primeiro["alimentacao_terceirizada"]["medicoes_iniciais"]
        assert medicoes["aguardando_envio_ue"] is None

        with patch("apps.sigpae.client.consultar") as consultar:
            service.obter_metricas()
            consultar.assert_not_called()

    def test_falha_de_banco_degrada_para_nulos(self) -> None:
        """Falha de conexão devolve o contrato com indicadores nulos."""
        with patch(
            "apps.sigpae.client.consultar",
            side_effect=psycopg.OperationalError("indisponivel"),
        ):
            resultado = service.obter_metricas()

        assert resultado["atualizado_em"] is None
        assert resultado["usuarios"]["com_acesso_ativo"] is None
        assert resultado["usuarios"]["por_tipo_perfil"]["codae"] is None
        medicoes = resultado["alimentacao_terceirizada"]["medicoes_iniciais"]
        assert medicoes["enviadas_pelas_unidades"] is None
