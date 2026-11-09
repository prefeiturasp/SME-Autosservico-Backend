"""Testes dos blocos de fechamento e conselho de classe do SGP."""

from datetime import date
from typing import Any
from unittest.mock import patch

import pytest

from apps.sgp import handler
from apps.sgp import mapper
from apps.sgp import parser
from apps.sgp import queries
from apps.sgp.periodo import SEGMENTO_EJA
from apps.sgp.periodo import Periodo

_FUND_MEDIO = Periodo(ano_letivo=2026, bimestre=2)
_EJA = Periodo(ano_letivo=2026, bimestre=1, segmento=SEGMENTO_EJA, semestre=2)


class TestPredicadoSegmento:
    """Cobre o predicado de segmento nas consultas filtradas."""

    @pytest.mark.parametrize(
        "sql",
        [
            queries.FECHAMENTO_POR_DRE_SITUACAO,
            queries.CONSELHO_CLASSE_POR_DRE_SITUACAO,
            queries.CONSELHO_CLASSE_PREVISTO_POR_DRE,
        ],
    )
    def test_segmento_e_semestre_sao_parametros(self, sql: str) -> None:
        """Fund./Médio (5, 6) e EJA (3 + semestre) vêm por parâmetro."""
        assert (
            "%(segmento)s = 'fundamental_medio' "
            "and t.modalidade_codigo in (5, 6)"
        ) in sql
        assert "t.modalidade_codigo = 3" in sql
        assert "t.semestre = %(semestre)s" in sql


class TestFechamento:
    """Cobre parser/mapper/handler do acompanhamento de fechamento."""

    def test_parser_agrupa_por_dre_e_situacao(self) -> None:
        """As linhas viram ``dre -> situacao -> quantidade``."""
        linhas: list[dict[str, Any]] = [
            {"dre": "BT", "situacao": 0, "quantidade": 10},
            {"dre": "BT", "situacao": 3, "quantidade": 7},
            {"dre": "CL", "situacao": 2, "quantidade": 4},
            {"dre": None, "situacao": 2, "quantidade": 99},
        ]

        assert parser.parse_por_dre_situacao(linhas) == {
            "BT": {0: 10, 3: 7},
            "CL": {2: 4},
        }

    def test_mapper_soma_dres_no_total_e_calcula_esperado(self) -> None:
        """Total geral = soma das DREs; esperado = soma das situações."""
        bloco = mapper.mapear_fechamento(
            {"CL": {2: 4, 4: 1}, "BT": {0: 10, 3: 7}}
        )

        assert bloco == {
            "esperado": 22,
            "nao_iniciados": 10,
            "processado_pendencias": 4,
            "processado_sucesso": 7,
            "processado_erro": 1,
            "por_dre": [
                {
                    "dre": "BT",
                    "previsto": 17,
                    "nao_iniciados": 10,
                    "processado_pendencias": 0,
                    "processado_sucesso": 7,
                    "processado_erro": 0,
                },
                {
                    "dre": "CL",
                    "previsto": 5,
                    "nao_iniciados": 0,
                    "processado_pendencias": 4,
                    "processado_sucesso": 0,
                    "processado_erro": 1,
                },
            ],
        }

    def test_mapper_sem_linhas_zera_tudo(self) -> None:
        """Sem consolidação no período, os buckets ficam zerados."""
        bloco = mapper.mapear_fechamento({})

        assert bloco["esperado"] == 0
        assert bloco["nao_iniciados"] == 0
        assert bloco["por_dre"] == []

    def test_handler_repassa_periodo_e_segmento(self) -> None:
        """O handler consulta com o SQL do segmento e parâmetros nomeados."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.return_value = [
                {"dre": "BT", "situacao": 2, "quantidade": 5}
            ]
            bloco = handler.obter_fechamento(_EJA)

        consultar.assert_called_once()
        sql, params = consultar.call_args.args
        assert sql == queries.FECHAMENTO_POR_DRE_SITUACAO
        assert params == {
            "ano_letivo": 2026,
            "bimestre": 1,
            "segmento": "eja",
            "semestre": 2,
        }
        assert bloco["processado_pendencias"] == 5


class TestConselhoClasse:
    """Cobre o cálculo de "não iniciados" do conselho de classe."""

    def test_parser_previsto_por_dre(self) -> None:
        """As linhas de matrículas viram ``dre -> previsto``."""
        linhas: list[dict[str, Any]] = [
            {"dre": "BT", "previsto": 424},
            {"dre": "CL", "previsto": None},
            {"dre": None, "previsto": 1},
        ]

        assert parser.parse_previsto_por_dre(linhas) == {"BT": 424, "CL": 0}

    def test_nao_iniciados_e_calculado_por_dre(self) -> None:
        """Não iniciados = previsto - (em andamento + concluído), por DRE."""
        bloco = mapper.mapear_conselho_classe(
            {"BT": {1: 60, 2: 334}, "CL": {1: 10}},
            {"BT": 424, "CL": 5, "G": 7},
        )

        assert bloco["por_dre"] == [
            {
                "dre": "BT",
                "previsto": 424,
                "nao_iniciados": 30,
                "em_andamento": 60,
                "processado_sucesso": 334,
            },
            {
                "dre": "CL",
                "previsto": 5,
                "nao_iniciados": 0,
                "em_andamento": 10,
                "processado_sucesso": 0,
            },
            {
                "dre": "G",
                "previsto": 7,
                "nao_iniciados": 7,
                "em_andamento": 0,
                "processado_sucesso": 0,
            },
        ]
        assert bloco["esperado"] == 436
        assert bloco["nao_iniciados"] == 37
        assert bloco["em_andamento"] == 70
        assert bloco["processado_sucesso"] == 334

    def test_handler_consulta_situacao_e_previsto(self) -> None:
        """O handler junta a consulta de situação com a de matrículas."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = [
                [{"dre": "BT", "situacao": 1, "quantidade": 387}],
                [{"dre": "BT", "previsto": 591}],
            ]
            bloco = handler.obter_conselho_classe(_FUND_MEDIO)

        assert consultar.call_count == 2
        sql_previsto = consultar.call_args_list[1].args[0]
        assert "consolidacao_matricula_turma" in sql_previsto
        assert bloco["em_andamento"] == 387
        assert bloco["nao_iniciados"] == 204
        assert bloco["esperado"] == 591


class TestPeriodos:
    """Cobre as opções do filtro de período."""

    def test_mapeia_modalidade_do_calendario_em_segmento(self) -> None:
        """Modalidade 1 vira Fund./Médio (sem semestre); 2 vira EJA."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.return_value = [
                {
                    "ano_letivo": 2026,
                    "modalidade": 1,
                    "semestre": 0,
                    "bimestre": 4,
                    "inicio": date(2026, 10, 5),
                    "fim": date(2026, 12, 18),
                },
                {
                    "ano_letivo": 2026,
                    "modalidade": 2,
                    "semestre": 2,
                    "bimestre": 1,
                    "inicio": date(2026, 7, 27),
                    "fim": date(2026, 9, 30),
                },
            ]
            periodos = handler.obter_periodos(2025, 2026)

        assert consultar.call_args.args[1] == {
            "ano_inicial": 2025,
            "ano_final": 2026,
        }
        assert periodos == [
            {
                "ano_letivo": 2026,
                "segmento": "fundamental_medio",
                "semestre": None,
                "bimestre": 4,
                "inicio": "2026-10-05",
                "fim": "2026-12-18",
            },
            {
                "ano_letivo": 2026,
                "segmento": "eja",
                "semestre": 2,
                "bimestre": 1,
                "inicio": "2026-07-27",
                "fim": "2026-09-30",
            },
        ]

    def test_ignora_modalidade_desconhecida(self) -> None:
        """Calendários fora de Fund./Médio e EJA não viram opção."""
        periodos = mapper.mapear_periodos(
            [
                {
                    "ano_letivo": 2026,
                    "modalidade": 3,
                    "semestre": None,
                    "bimestre": 1,
                    "inicio": date(2026, 2, 1),
                    "fim": date(2026, 4, 30),
                }
            ]
        )

        assert periodos == []
