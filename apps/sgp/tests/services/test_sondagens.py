"""Testes do bloco de sondagens do SGP."""

from unittest.mock import patch

from apps.sgp import handler
from apps.sgp import mapper
from apps.sgp import parser
from apps.sgp import queries


class TestParser:
    """Cobre a interpretação da linha de sondagens."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, realizadas e esperadas voltam zeradas."""
        assert parser.parse_sondagens([]) == {
            "realizadas": 0,
            "esperadas": 0,
        }

    def test_mapeia_realizadas_e_esperadas(self) -> None:
        """Os campos da linha viram realizadas/esperadas."""
        linhas = [{"esperadas": 2683, "realizadas": 1243}]

        assert parser.parse_sondagens(linhas) == {
            "realizadas": 1243,
            "esperadas": 2683,
        }


class TestMapper:
    """Cobre a montagem do bloco de sondagens."""

    def test_preserva_realizadas_e_esperadas(self) -> None:
        """O mapper repassa realizadas e esperadas."""
        bloco = mapper.mapear_sondagens(
            {"realizadas": 1243, "esperadas": 2683}
        )

        assert bloco == {"realizadas": 1243, "esperadas": 2683}


class TestHandler:
    """Cobre a orquestração do handler de sondagens."""

    def test_consulta_com_ano_e_bimestre(self) -> None:
        """O handler passa ano letivo e bimestre para a consulta."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.return_value = [{"esperadas": 2683, "realizadas": 1243}]
            bloco = handler.obter_sondagens(2026, 2)

        consultar.assert_called_once_with(
            queries.SONDAGENS_REALIZADAS_ESPERADAS, (2026, 2)
        )
        assert bloco == {"realizadas": 1243, "esperadas": 2683}
