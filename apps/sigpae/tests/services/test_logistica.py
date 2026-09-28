"""Testes do bloco de logística (pré-recebimento) do SIGPAE."""

from unittest.mock import patch

from apps.sigpae import handler
from apps.sigpae import parser


class TestParserLogistica:
    """Cobre os parsers de linha única da logística."""

    def test_sem_linhas_zera_campos(self) -> None:
        """Sem linhas, todos os campos voltam zerados."""
        assert parser.parse_cronogramas_entregas([]) == {
            "aguardando": 0,
            "enviadas": 0,
            "aprovadas": 0,
        }
        assert parser.parse_fornecedores_distribuidores([]) == {
            "cadastradas": 0,
            "ativas": 0,
        }

    def test_ignora_colunas_extras(self) -> None:
        """Só os campos do card são considerados."""
        linha = [{"cadastrados": 7, "aprovados": 4, "ignorar": 99}]
        resultado = parser.parse_layouts_embalagens(linha)

        assert resultado["cadastrados"] == 7
        assert resultado["aprovados"] == 4
        assert "ignorar" not in resultado


class TestHandlerLogistica:
    """Cobre os handlers da logística."""

    def test_cronogramas_consulta_e_monta(self) -> None:
        """Handler devolve o agregado de cronogramas."""
        with patch(
            "apps.sigpae.client.consultar",
            return_value=[{"aguardando": 2, "enviadas": 3, "aprovadas": 1}],
        ):
            assert handler.obter_cronogramas_entregas() == {
                "aguardando": 2,
                "enviadas": 3,
                "aprovadas": 1,
            }

    def test_fornecedores_consulta_e_monta(self) -> None:
        """Handler devolve o agregado de fornecedores."""
        with patch(
            "apps.sigpae.client.consultar",
            return_value=[{"cadastradas": 8, "ativas": 5}],
        ):
            assert handler.obter_fornecedores_distribuidores() == {
                "cadastradas": 8,
                "ativas": 5,
            }
