"""Testes do bloco de empresas terceirizadas do SIGPAE."""

from unittest.mock import patch

from apps.sigpae import handler
from apps.sigpae import mapper
from apps.sigpae import parser


class TestParserEmpresas:
    """Cobre a interpretação do agregado de empresas."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, cadastradas e ativas voltam zeradas."""
        assert parser.parse_empresas_terceirizadas([]) == {
            "cadastradas": 0,
            "ativas": 0,
        }


class TestMapperEmpresas:
    """Cobre a montagem do bloco de empresas."""

    def test_mapeia_cadastradas_e_ativas(self) -> None:
        """O mapper preserva cadastradas e ativas."""
        dados = {"cadastradas": 7, "ativas": 5}

        assert mapper.mapear_empresas_terceirizadas(dados) == dados


class TestHandlerEmpresas:
    """Cobre o handler de empresas."""

    def test_consulta_e_mapeia(self) -> None:
        """O handler consulta o agregado e devolve o bloco."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.return_value = [{"cadastradas": 7, "ativas": 5}]
            bloco = handler.obter_empresas_terceirizadas()

        assert bloco == {"cadastradas": 7, "ativas": 5}
