"""Testes do bloco de usuários do SGP."""

from unittest.mock import patch

from apps.sgp import handler
from apps.sgp import mapper
from apps.sgp import parser


class TestParser:
    """Cobre a interpretação das linhas cruas do banco."""

    def test_acesso_ativo_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, os contadores voltam zerados."""
        assert parser.parse_acesso_ativo([]) == {
            "valor": 0,
            "variacao_30_dias": 0,
        }

    def test_acesso_ativo_mapeia_total_e_ativos(self) -> None:
        """``total`` vira ``valor`` e ``ativos_30_dias`` a variação."""
        linhas = [{"total": 8398, "ativos_30_dias": 453}]

        assert parser.parse_acesso_ativo(linhas) == {
            "valor": 8398,
            "variacao_30_dias": 453,
        }

    def test_de_unidades_mapeia_total_e_diretorias(self) -> None:
        """``diretorias`` vira ``diretorias_regionais``."""
        linhas = [{"total": 200, "diretorias": 13}]

        assert parser.parse_de_unidades(linhas) == {
            "total": 200,
            "diretorias_regionais": 13,
        }


class TestMapper:
    """Cobre a montagem do bloco de usuários."""

    def test_gaps_viram_null(self) -> None:
        """``unicos_por_dia`` e ``acessos_por_hora`` são sempre None."""
        bloco = mapper.mapear_usuarios(
            {"valor": 8398, "variacao_30_dias": 453},
            {"total": 200, "diretorias_regionais": 13},
        )

        assert bloco["com_acesso_ativo"] == {
            "valor": 8398,
            "variacao_30_dias": 453,
        }
        assert bloco["de_unidades_educacionais"]["diretorias_regionais"] == 13
        assert bloco["unicos_por_dia"] is None
        assert bloco["acessos_por_hora"] is None


class TestHandler:
    """Cobre a orquestração das consultas de usuários."""

    def test_orquestra_as_duas_consultas(self) -> None:
        """O handler compõe acesso ativo e unidades no bloco final."""
        with patch("apps.sgp.client.consultar") as consultar:
            consultar.side_effect = [
                [{"total": 8398, "ativos_30_dias": 453}],
                [{"total": 200, "diretorias": 13}],
            ]
            bloco = handler.obter_usuarios()

        assert bloco["com_acesso_ativo"]["valor"] == 8398
        assert bloco["de_unidades_educacionais"]["total"] == 200
