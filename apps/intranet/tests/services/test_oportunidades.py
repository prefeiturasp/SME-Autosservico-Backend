"""Testes do bloco de Oportunidades e Recrutamento do Intranet."""

from unittest.mock import patch

from apps.intranet import handler
from apps.intranet import parser


class TestParser:
    """Cobre a interpretação da linha de Oportunidades."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, os quatro contadores voltam zerados."""
        assert set(parser.parse_oportunidades([]).values()) == {0}


class TestHandler:
    """Cobre a orquestração e o mapeamento de Oportunidades."""

    def test_renomeia_para_o_contrato(self) -> None:
        """``oportunidades_cadastradas`` vira ``cadastradas``."""
        with patch("apps.intranet.client.consultar") as consultar:
            consultar.return_value = [
                {
                    "oportunidades_cadastradas": 2,
                    "cvs_cadastrados": 3,
                    "inscricoes_realizadas": 3,
                    "contratacoes_efetivadas": 0,
                }
            ]
            bloco = handler.obter_oportunidades()

        assert bloco == {
            "cadastradas": 2,
            "cvs_cadastrados": 3,
            "inscricoes_realizadas": 3,
            "contratacoes_efetivadas": 0,
        }
