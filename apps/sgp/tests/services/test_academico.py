"""Testes dos blocos de fechamento e conselho de classe do SGP."""

from unittest.mock import patch

from apps.sgp import handler
from apps.sgp import mapper
from apps.sgp import parser


class TestFechamento:
    """Cobre parser/mapper/handler do acompanhamento de fechamento."""

    def test_parser_agrupa_por_situacao(self) -> None:
        """As linhas viram um dicionário ``situacao -> quantidade``."""
        linhas = [
            {"situacao": 0, "quantidade": 10},
            {"situacao": 3, "quantidade": 7},
        ]

        assert parser.parse_por_situacao(linhas) == {0: 10, 3: 7}

    def test_mapper_completa_buckets_ausentes_com_zero(self) -> None:
        """Situações ausentes viram zero, na nomenclatura do card."""
        bloco = mapper.mapear_fechamento({0: 8398, 3: 7530})

        assert bloco == {
            "nao_iniciados": 8398,
            "processado_pendencias": 0,
            "processado_sucesso": 7530,
            "processado_erro": 0,
        }

    def test_handler_repassa_ano_e_bimestre(self) -> None:
        """O handler consulta com os parâmetros de período."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.return_value = [{"situacao": 2, "quantidade": 5}]
            bloco = handler.obter_fechamento(2026, 2)

        consultar.assert_called_once()
        assert consultar.call_args.args[1] == (2026, 2)
        assert bloco["processado_pendencias"] == 5


class TestConselhoClasse:
    """Cobre o cálculo de "não iniciados" do conselho de classe."""

    def test_nao_iniciados_e_calculado(self) -> None:
        """Nao iniciados = alunos ativos - (em andamento + concluido)."""
        bloco = mapper.mapear_conselho_classe({1: 387, 2: 1889}, 2480)

        assert bloco == {
            "nao_iniciados": 204,
            "em_andamento": 387,
            "processado_sucesso": 1889,
        }

    def test_nao_iniciados_nunca_negativo(self) -> None:
        """Se os buckets excedem os ativos, "não iniciados" é zero."""
        bloco = mapper.mapear_conselho_classe({1: 10, 2: 10}, 5)

        assert bloco["nao_iniciados"] == 0

    def test_handler_consulta_situacao_e_alunos_ativos(self) -> None:
        """O handler junta a query de situação com a de alunos ativos."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = [
                [{"situacao": 1, "quantidade": 387}],
                [{"alunos_ativos": 591}],
            ]
            bloco = handler.obter_conselho_classe(2026, 2)

        assert bloco["em_andamento"] == 387
        assert bloco["nao_iniciados"] == 204
