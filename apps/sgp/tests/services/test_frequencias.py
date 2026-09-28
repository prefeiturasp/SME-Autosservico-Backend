"""Testes do bloco de frequências do SGP."""

from unittest.mock import patch

from apps.sgp import handler
from apps.sgp import mapper
from apps.sgp import parser
from apps.sgp import queries


class TestParser:
    """Cobre a interpretação da linha de frequências."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, lançadas e esperadas voltam zeradas."""
        assert parser.parse_frequencias([]) == {
            "lancadas": 0,
            "esperadas": 0,
        }

    def test_mapeia_lancadas_e_esperadas(self) -> None:
        """Os campos da linha viram lançadas/esperadas."""
        linhas = [{"esperadas": 21760, "lancadas": 18432}]

        assert parser.parse_frequencias(linhas) == {
            "lancadas": 18432,
            "esperadas": 21760,
        }


class TestMapper:
    """Cobre a montagem do bloco de frequências."""

    def test_calcula_percentual(self) -> None:
        """O percentual é lançadas/esperadas em uma casa decimal."""
        bloco = mapper.mapear_frequencias(
            {"lancadas": 18432, "esperadas": 21760}
        )

        assert bloco == {
            "lancadas": 18432,
            "esperadas": 21760,
            "percentual": 84.7,
        }

    def test_percentual_zero_quando_esperadas_zero(self) -> None:
        """Sem esperadas, o percentual é 0 (evita divisão por zero)."""
        bloco = mapper.mapear_frequencias({"lancadas": 0, "esperadas": 0})

        assert bloco == {"lancadas": 0, "esperadas": 0, "percentual": 0.0}


class TestHandler:
    """Cobre a orquestração do handler de frequências."""

    def test_consulta_com_ano_e_bimestre(self) -> None:
        """O handler passa ano letivo e bimestre para a consulta."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.return_value = [{"esperadas": 21760, "lancadas": 18432}]
            bloco = handler.obter_frequencias(2026, 2)

        consultar.assert_called_once_with(
            queries.FREQUENCIAS_LANCADAS_ESPERADAS, (2026, 2)
        )
        assert bloco["lancadas"] == 18432
        assert bloco["esperadas"] == 21760
