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
            "novos_30_dias": 0,
        }

    def test_por_tipo_perfil_normaliza_visao(self) -> None:
        """A visão é normalizada para maiúsculas."""
        linhas = [
            {"visao": "codae", "total_usuarios": 3},
            {"visao": "UE", "total_usuarios": 5},
        ]

        assert parser.parse_por_tipo_perfil(linhas) == {"CODAE": 3, "UE": 5}

    def test_comparativo_desempilha_os_12_baldes(self) -> None:
        """Os 12 campos viram 3 valores por período; ausentes = 0."""
        linha = [{"dia_1": 1, "dia_2": 2, "dia_3": 3, "trimestre_2": 9}]

        resultado = parser.parse_comparativo_acessos(linha)

        assert resultado["dia"] == [1, 2, 3]
        assert resultado["trimestre"] == [0, 9, 0]
        assert resultado["quinzena"] == [0, 0, 0]

    def test_comparativo_sem_linhas_zera(self) -> None:
        """Sem linhas, todos os baldes voltam zerados."""
        resultado = parser.parse_comparativo_acessos([])

        assert resultado == {
            "dia": [0, 0, 0],
            "quinzena": [0, 0, 0],
            "mes": [0, 0, 0],
            "trimestre": [0, 0, 0],
        }


class TestMapper:
    """Cobre a montagem do bloco de contrato."""

    def test_monta_bloco_com_acessos_e_perfis(self) -> None:
        """Acesso/acessos preenchem o bloco; perfis ausentes viram zero."""
        comparativo = mapper.mapear_comparativo_acessos(
            {
                "dia": [10, 25, 15],
                "quinzena": [0, 0, 0],
                "mes": [0, 0, 0],
                "trimestre": [0, 0, 0],
            }
        )
        bloco = mapper.mapear_usuarios(
            {"total": 10, "ativos_30_dias": 4, "novos_30_dias": 2},
            {"unicos_por_dia": 5, "acessos_hoje": 7},
            {"CODAE": 3},
            comparativo,
        )

        assert bloco["com_acesso_ativo"] == {
            "total": 10,
            "ativos_30_dias": 4,
            "novos_30_dias": 2,
        }
        assert bloco["unicos_por_dia"] == 5
        assert bloco["acessos_hoje"] == 7
        assert bloco["por_tipo_perfil"] == {
            "codae": 3,
            "dre": 0,
            "ue": 0,
            "empresa": 0,
        }

    def test_comparativo_marca_o_pico_e_rotula(self) -> None:
        """O maior balde vira pico; sem acessos, ninguém é pico."""
        comparativo = mapper.mapear_comparativo_acessos(
            {
                "dia": [10, 25, 15],
                "quinzena": [0, 0, 0],
                "mes": [1, 1, 1],
                "trimestre": [5, 5, 9],
            }
        )

        dia = comparativo["dia"]["buckets"]
        assert dia[0] == {"label": "Dia 1", "value": 10, "isPeak": False}
        assert dia[1] == {"label": "Dia 2", "value": 25, "isPeak": True}
        # Sem acessos: nenhum balde é pico.
        assert all(not b["isPeak"] for b in comparativo["quinzena"]["buckets"])
        # Empate: só o primeiro máximo é pico.
        mes = comparativo["mes"]["buckets"]
        assert [b["isPeak"] for b in mes] == [True, False, False]
        # Rótulo de trimestre usa "Mês".
        assert comparativo["trimestre"]["buckets"][2] == {
            "label": "Mês 3",
            "value": 9,
            "isPeak": True,
        }


class TestHandler:
    """Cobre a orquestração das consultas."""

    def test_orquestra_queries_parser_e_mapper(self) -> None:
        """O handler compõe as duas consultas no bloco final."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 10, "ativos_30_dias": 4, "novos_30_dias": 2}],
                [{"unicos_por_dia": 5, "acessos_hoje": 7}],
                [{"visao": "CODAE", "total_usuarios": 3}],
                [{"dia_3": 42}],
            ]
            bloco = handler.obter_usuarios()

        assert bloco["com_acesso_ativo"]["total"] == 10
        assert bloco["acessos_hoje"] == 7
        assert bloco["por_tipo_perfil"]["codae"] == 3
        assert bloco["comparativo_acessos"]["dia"]["buckets"][2] == {
            "label": "Dia 3",
            "value": 42,
            "isPeak": True,
        }


class TestService:
    """Cobre cache e degradação do serviço."""

    def test_sucesso_preenche_e_cacheia(self) -> None:
        """Primeira chamada consulta o banco e cacheia o resultado."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 10, "ativos_30_dias": 4, "novos_30_dias": 2}],
                [{"unicos_por_dia": 5, "acessos_hoje": 7}],
                [{"visao": "CODAE", "total_usuarios": 3}],
                [{"dia_1": 1, "dia_2": 2, "dia_3": 3}],
                [
                    {
                        "status": "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                        "total": 16,
                    }
                ],
                [
                    {
                        "total_cadastrados": 6,
                        "homologados": 0,
                        "solicitacoes_no_mes": 0,
                        "solicitacoes_no_ano": 0,
                    }
                ],
                [{"cadastradas": 7, "ativas": 5}],
                [
                    {
                        "periodo": "quinzena",
                        "total": 5,
                        "autorizadas": 2,
                        "aguardando": 3,
                        "negadas": 0,
                        "canceladas": 0,
                    }
                ],
                [
                    {
                        "periodo": "quinzena",
                        "total": 19,
                        "autorizadas": 10,
                        "aguardando": 0,
                        "negadas": 9,
                        "canceladas": 0,
                    }
                ],
                [{"aguardando": 2, "enviadas": 3, "aprovadas": 1}],
                [
                    {
                        "cadastradas": 10,
                        "aprovadas": 6,
                        "em_analise": 3,
                        "pendentes_correcao": 1,
                    }
                ],
                [{"cadastradas": 8, "ativas": 5}],
                [
                    {
                        "cadastrados": 7,
                        "aprovados": 4,
                        "aguardando_codae": 2,
                        "pendentes_correcao": 1,
                    }
                ],
            ]
            primeiro = service.obter_metricas()

        assert primeiro["atualizado_em"] is not None
        assert primeiro["usuarios"]["com_acesso_ativo"]["total"] == 10
        alimentacao = primeiro["alimentacao_terceirizada"]
        assert alimentacao["medicoes_iniciais"]["aguardando_envio_ue"] == 16
        dietas = alimentacao["solicitacoes_dietas_especiais"]
        assert dietas["quinzena"]["autorizadas"] == 2
        assert dietas["dia"]["total"] == 0
        alimentacoes = alimentacao["solicitacoes_alimentacoes"]
        assert alimentacoes["quinzena"]["negadas"] == 9
        assert alimentacoes["dia"]["total"] == 0
        logistica = primeiro["logistica"]
        assert logistica["cronogramas_entregas"]["enviadas"] == 3
        assert logistica["fichas_tecnicas_produtos"]["cadastradas"] == 10
        assert logistica["fornecedores_distribuidores"]["ativas"] == 5
        assert logistica["layouts_embalagens"]["aprovados"] == 4

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
        alimentacao = resultado["alimentacao_terceirizada"]
        medicoes = alimentacao["medicoes_iniciais"]
        assert medicoes["enviadas_pelas_unidades"] is None
        assert alimentacao["solicitacoes_dietas_especiais"] is None
        assert alimentacao["solicitacoes_alimentacoes"] is None
        assert resultado["logistica"]["cronogramas_entregas"] is None
        assert resultado["logistica"]["layouts_embalagens"] is None
