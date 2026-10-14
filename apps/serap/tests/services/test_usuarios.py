"""Testes do bloco de usuários do SERAp Estudantes."""

from unittest.mock import patch

from apps.serap import handler
from apps.serap import mapper
from apps.serap import parser
from apps.serap import queries


class TestParser:
    """Cobre a interpretação da linha crua do banco."""

    def test_acesso_ativo_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, os contadores voltam zerados."""
        assert parser.parse_acesso_ativo([]) == {
            "valor": 0,
            "variacao_30_dias": 0,
        }

    def test_acesso_ativo_mapeia_total_e_ativos(self) -> None:
        """``total`` vira ``valor`` e ``novos_30_dias`` a variação."""
        linhas = [{"total": 387153, "novos_30_dias": 1200}]

        assert parser.parse_acesso_ativo(linhas) == {
            "valor": 387153,
            "variacao_30_dias": 1200,
        }


class TestMapper:
    """Cobre a montagem do bloco de usuários."""

    def test_gaps_viram_null(self) -> None:
        """``unicos_por_dia`` e ``acessos_por_hora`` são sempre None."""
        bloco = mapper.mapear_usuarios(
            {"valor": 387153, "variacao_30_dias": 1200}
        )

        assert bloco["com_acesso_ativo"] == {
            "valor": 387153,
            "variacao_30_dias": 1200,
        }
        assert bloco["unicos_por_dia"] is None
        assert bloco["acessos_por_hora"] is None


class TestHandler:
    """Cobre a consulta do bloco de usuários."""

    def test_consulta_acesso_ativo(self) -> None:
        """O handler executa a query de acesso ativo e monta o bloco."""
        with patch("apps.serap.client.consultar") as consultar:
            consultar.return_value = [{"total": 10, "novos_30_dias": 3}]
            bloco = handler.obter_usuarios()

        consultar.assert_called_once_with(queries.USUARIOS_ACESSO_ATIVO)
        assert bloco["com_acesso_ativo"]["valor"] == 10
        assert bloco["com_acesso_ativo"]["variacao_30_dias"] == 3
