"""Testes do bloco de produtos homologados do SIGPAE."""

from unittest.mock import patch

from apps.sigpae import handler
from apps.sigpae import mapper
from apps.sigpae import parser


class TestParserProdutos:
    """Cobre a interpretação do agregado de produtos."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, os quatro indicadores voltam zerados."""
        assert parser.parse_produtos_homologados([]) == {
            "total_cadastrados": 0,
            "homologados": 0,
            "solicitacoes_no_mes": 0,
            "solicitacoes_no_ano": 0,
        }


class TestMapperProdutos:
    """Cobre a montagem do bloco de produtos homologados."""

    def test_mapeia_os_quatro_indicadores(self) -> None:
        """O mapper preserva os quatro indicadores."""
        dados = {
            "total_cadastrados": 6,
            "homologados": 2,
            "solicitacoes_no_mes": 1,
            "solicitacoes_no_ano": 5,
        }

        assert mapper.mapear_produtos_homologados(dados) == dados


class TestHandlerProdutos:
    """Cobre o handler de produtos homologados."""

    def test_consulta_e_mapeia(self) -> None:
        """O handler consulta o agregado e devolve o bloco."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.return_value = [
                {
                    "total_cadastrados": 6,
                    "homologados": 0,
                    "solicitacoes_no_mes": 0,
                    "solicitacoes_no_ano": 0,
                }
            ]
            bloco = handler.obter_produtos_homologados()

        assert bloco["total_cadastrados"] == 6
