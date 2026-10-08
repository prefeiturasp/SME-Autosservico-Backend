"""Testes do bloco de KPIs de usuário do Intranet."""

from unittest.mock import patch

from apps.intranet import handler
from apps.intranet import mapper
from apps.intranet import parser
from apps.intranet import queries


class TestParser:
    """Cobre a interpretação da linha de KPIs."""

    def test_sem_linhas_retorna_zeros(self) -> None:
        """Sem linhas, os contadores voltam zerados."""
        assert parser.parse_kpis([]) == {
            "com_acesso_ativo": 0,
            "unicos_hoje": 0,
        }

    def test_nulos_viram_zero(self) -> None:
        """``NULL`` do MySQL vira 0."""
        linhas = [{"com_acesso_ativo": 1, "unicos_hoje": None}]

        assert parser.parse_kpis(linhas) == {
            "com_acesso_ativo": 1,
            "unicos_hoje": 0,
        }


class TestMapper:
    """Cobre a montagem do bloco ``kpis``."""

    def test_acessos_hoje_reaproveita_unicos_e_tendencia_nula(self) -> None:
        """Sem histórico de login, acessos hoje = únicos e sem tendência."""
        bloco = mapper.mapear_kpis({"com_acesso_ativo": 1, "unicos_hoje": 4})

        assert bloco["acesso_ativo"] == {
            "valor": 1,
            "tendencia": None,
            "tendencia_label": None,
        }
        assert bloco["usuarios_unicos"]["valor"] == 4
        assert bloco["acessos_hoje"]["valor"] == 4
        assert bloco["acessos_hoje"]["tendencia"] is None


class TestHandler:
    """Cobre a orquestração da consulta de KPIs."""

    def test_consulta_e_monta_bloco(self) -> None:
        """O handler consulta uma vez e devolve o bloco do contrato."""
        with patch("apps.intranet.client.consultar") as consultar:
            consultar.return_value = [
                {"com_acesso_ativo": 1, "unicos_hoje": 0}
            ]
            bloco = handler.obter_kpis()

        consultar.assert_called_once_with(queries.KPIS_USUARIOS)
        assert bloco["acesso_ativo"]["valor"] == 1
        assert bloco["usuarios_unicos"]["valor"] == 0
