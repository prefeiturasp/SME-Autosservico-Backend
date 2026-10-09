"""Testes dos blocos de métricas do SIG-Escola (parser, mapper, handler)."""

from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest

from apps.sigescola import handler
from apps.sigescola import mapper
from apps.sigescola import parser
from apps.sigescola import queries

_FILTRO = {
    "inicio": date(2026, 5, 1),
    "fim": date(2026, 9, 1),
    "dre": None,
    "ue": None,
}

_LOGINS = {
    "unicos_hoje": 2,
    "acessos_hoje": 2,
    "usuarios_dia_30_dias": 78,
    "acessos_30_dias": 127,
}

_UNIDADE = {"codigo_eol": "019715", "tipo_unidade": "EMEF", "nome": "ADALGIZA"}


class TestParser:
    """Cobre a interpretação das linhas cruas do banco."""

    def test_por_situacao_ignora_status_nulo(self) -> None:
        """Linhas sem status não entram no dicionário."""
        linhas: list[dict[str, Any]] = [
            {"situacao": "GERADO", "quantidade": 35},
            {"situacao": None, "quantidade": 9},
        ]

        assert parser.parse_por_situacao(linhas) == {"GERADO": 35}

    def test_sem_linhas_vira_zero(self) -> None:
        """Consulta vazia devolve zero nos escalares."""
        assert parser.parse_inteiro([], "total") == 0
        assert parser.parse_valor([], "valor") == pytest.approx(0.0)

    def test_valor_converte_decimal_para_float(self) -> None:
        """O ``Decimal`` do psycopg vira ``float``."""
        linhas = [{"valor": Decimal("578497.91")}]

        assert parser.parse_valor(linhas, "valor") == pytest.approx(578497.91)

    def test_logins(self) -> None:
        """Os contadores de login são lidos da linha única; vazio vira 0."""
        assert parser.parse_logins([dict(_LOGINS)]) == _LOGINS
        assert parser.parse_logins([]) == dict.fromkeys(_LOGINS, 0)

    def test_periodos_e_unidades(self) -> None:
        """Períodos e unidades saem com os campos esperados."""
        periodo = {
            "referencia": "2026.3",
            "data_inicio": date(2026, 9, 2),
            "data_fim": None,
        }

        assert parser.parse_periodos([dict(periodo)]) == [periodo]
        assert parser.parse_unidades([dict(_UNIDADE)]) == [_UNIDADE]


class TestMapper:
    """Cobre a montagem dos blocos do contrato."""

    def test_plano_anual_por_status(self) -> None:
        """Os três status viram os buckets; NAO_INICIADO fica fora."""
        bloco = mapper.mapear_plano_anual(
            {
                "EM_ELABORACAO": 83,
                "GERADO": 35,
                "EM_RETIFICACAO": 46,
                "NAO_INICIADO": 1,
            }
        )

        assert bloco == {
            "em_andamento": 83,
            "finalizados": 35,
            "em_retificacao": 46,
        }

    def test_plano_anual_sem_dados_zera(self) -> None:
        """Sem PAAs na janela, os três buckets são zero."""
        assert mapper.mapear_plano_anual({}) == {
            "em_andamento": 0,
            "finalizados": 0,
            "em_retificacao": 0,
        }

    def test_prestacao_de_contas(self) -> None:
        """Enviadas somam tudo menos NAO_RECEBIDA e NAO_APRESENTADA."""
        bloco = mapper.mapear_prestacao_de_contas(
            ues_aptas=1650,
            por_situacao={
                "EM_ANALISE": 2,
                "APROVADA": 3,
                "NAO_RECEBIDA": 2,
                "NAO_APRESENTADA": 1,
            },
            creditos=118502864.0,
            despesas=578497.914,
            demonstrativos=7,
            devolucao=0.0,
        )

        assert bloco == {
            "ues_aptas": 1650,
            "enviadas_ou_em_andamento": 5,
            "creditos_disponiveis": 118502864.0,
            "despesas_registradas": 578497.91,
            "demonstrativos_gerados": 7,
            "devolucao_ao_tesouro": 0.0,
        }

    def test_situacao_patrimonial(self) -> None:
        """Quantidade e valor dos bens, com o valor em duas casas."""
        assert mapper.mapear_situacao_patrimonial(7, 20199.904) == {
            "quantidade_bens_produzidos": 7,
            "valor_bens_produzidos": 20199.9,
        }

    def test_usuarios_compara_hoje_com_a_media(self) -> None:
        """78 pares (usuário, dia) em 30 dias = média 2,6: hoje 2 = -23,1%.

        127 acessos em 30 dias = média 4,23: hoje 2 = -52,8%.
        """
        assert mapper.mapear_usuarios(28, 2, _LOGINS) == {
            "com_acesso_ativo": {"valor": 28, "variacao_30_dias": 2},
            "unicos_por_dia": {
                "valor": 2,
                "variacao_percentual_30_dias": -23.1,
            },
            "acessos_hoje": {
                "valor": 2,
                "variacao_percentual_30_dias": -52.8,
            },
        }

    def test_usuarios_sem_historico_nao_divide_por_zero(self) -> None:
        """Sem logins nos 30 dias anteriores, a variação é zero."""
        logins = {
            "unicos_hoje": 1,
            "acessos_hoje": 1,
            "usuarios_dia_30_dias": 0,
            "acessos_30_dias": 0,
        }
        bloco = mapper.mapear_usuarios(0, 0, logins)

        assert bloco["unicos_por_dia"][
            "variacao_percentual_30_dias"
        ] == pytest.approx(0.0)
        assert bloco["acessos_hoje"][
            "variacao_percentual_30_dias"
        ] == pytest.approx(0.0)

    def test_unidades_juntam_tipo_e_nome(self) -> None:
        """O rótulo da UE é ``TIPO NOME``; sem tipo, só o nome."""
        unidades = mapper.mapear_unidades(
            [
                _UNIDADE,
                {"codigo_eol": "000001", "tipo_unidade": None, "nome": "X"},
            ]
        )

        assert unidades == [
            {"codigo_eol": "019715", "nome": "EMEF ADALGIZA"},
            {"codigo_eol": "000001", "nome": "X"},
        ]


class TestHandler:
    """Cobre a orquestração das consultas de cada bloco."""

    def test_periodos(self) -> None:
        """Os períodos vêm da consulta sem parâmetros."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.return_value = [
                {
                    "referencia": "2026.3",
                    "data_inicio": date(2026, 9, 2),
                    "data_fim": None,
                }
            ]
            periodos = handler.obter_periodos()

        consultar.assert_called_once_with(queries.PERIODOS)
        assert periodos[0]["referencia"] == "2026.3"

    def test_unidades_da_dre(self) -> None:
        """As UEs são buscadas pelo código EOL da DRE."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.return_value = [dict(_UNIDADE)]
            unidades = handler.obter_unidades("108100")

        consultar.assert_called_once_with(
            queries.UNIDADES_DA_DRE, {"dre": "108100"}
        )
        assert unidades == [{"codigo_eol": "019715", "nome": "EMEF ADALGIZA"}]

    def test_usuarios(self) -> None:
        """Duas consultas sem filtro: cadastro de usuários e log de login."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 28, "novos_30_dias": 2}],
                [dict(_LOGINS)],
            ]
            bloco = handler.obter_usuarios()

        assert [c.args for c in consultar.call_args_list] == [
            (queries.USUARIOS_ACESSO_ATIVO,),
            (queries.USUARIOS_LOGINS,),
        ]
        assert bloco["com_acesso_ativo"] == {
            "valor": 28,
            "variacao_30_dias": 2,
        }
        assert bloco["acessos_hoje"]["valor"] == 2

    def test_plano_anual_usa_o_filtro(self) -> None:
        """A consulta de PAA recebe o filtro inteiro."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.return_value = [{"situacao": "GERADO", "quantidade": 35}]
            bloco = handler.obter_plano_anual(_FILTRO)

        consultar.assert_called_once_with(queries.PAA_POR_STATUS, _FILTRO)
        assert bloco["finalizados"] == 35

    def test_prestacao_de_contas_na_ordem(self) -> None:
        """As seis consultas do card rodam em ordem, com o mesmo filtro."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 1650}],
                [{"situacao": "EM_ANALISE", "quantidade": 2}],
                [{"valor": Decimal("118502864.00")}],
                [{"valor": Decimal("578497.91")}],
                [{"total": 7}],
                [{"valor": Decimal("0")}],
            ]
            bloco = handler.obter_prestacao_de_contas(_FILTRO)

        assert [c.args[0] for c in consultar.call_args_list] == [
            queries.UES_APTAS,
            queries.PRESTACOES_POR_STATUS,
            queries.CREDITOS_DISPONIVEIS,
            queries.DESPESAS_REGISTRADAS,
            queries.DEMONSTRATIVOS_GERADOS,
            queries.DEVOLUCAO_AO_TESOURO,
        ]
        assert all(c.args[1] == _FILTRO for c in consultar.call_args_list)
        assert bloco["enviadas_ou_em_andamento"] == 2
        assert bloco["creditos_disponiveis"] == pytest.approx(118502864.0)

    def test_situacao_patrimonial(self) -> None:
        """Quantidade e valor saem da mesma linha."""
        with patch("apps.sigescola.client.consultar") as consultar:
            consultar.return_value = [
                {"quantidade": 7, "valor": Decimal("20199.90")}
            ]
            bloco = handler.obter_situacao_patrimonial(_FILTRO)

        consultar.assert_called_once_with(queries.BENS_PRODUZIDOS, _FILTRO)
        assert bloco == {
            "quantidade_bens_produzidos": 7,
            "valor_bens_produzidos": 20199.9,
        }
