"""Testes do bloco de Ordem de Inscrição do Intranet (números do QA)."""

from datetime import datetime
from unittest.mock import patch

from apps.intranet import handler
from apps.intranet import mapper
from apps.intranet import parser
from apps.intranet import queries
from apps.intranet.handler import Janela

_JANELA: Janela = {"inicio": datetime(2026, 9, 7), "fim": None}
_JANELA_MES: Janela = {
    "inicio": datetime(2026, 9, 1),
    "fim": datetime(2026, 10, 1),
}


class TestParser:
    """Cobre a interpretação do status geral."""

    def test_status_geral_sem_realizados(self) -> None:
        """Ordem de Inscrição não tem "realizados"."""
        linhas = [{"cadastrados": 6, "ativos": 0, "encerrados": 6}]

        assert parser.parse_status_ordem(linhas) == {
            "cadastrados": 6,
            "ativos": 0,
            "encerrados": 6,
        }


class TestMapper:
    """Cobre a montagem do bloco ``ordem_inscricao``."""

    def test_monta_bloco_com_os_quatro_cards(self) -> None:
        """Status geral sem "realizados" e cards no formato label/value."""
        bloco = mapper.mapear_ordem_inscricao(
            {"cadastrados": 6, "ativos": 0, "encerrados": 6},
            {"data": 31, "periodo": 2, "premio": 2},
            {"servidor": 31, "estagiario": 4},
            {"DRE de teste": 20, "DRE Pirituba": 2},
        )

        assert bloco["status_geral"] == {
            "cadastrados": 6,
            "ativos": 0,
            "encerrados": 6,
        }
        assert bloco["por_tipo"][0] == {
            "label": "Data específica",
            "value": 31,
        }
        assert sum(item["value"] for item in bloco["por_ganhador"]) == 35
        assert bloco["por_dre"][0] == {"label": "DRE de teste", "value": 20}


class TestHandler:
    """Cobre a orquestração das consultas de Ordem de Inscrição."""

    def test_por_dre_usa_janela_do_mes(self) -> None:
        """Tipo/ganhador usam o período; "por DRE" usa a janela do mês."""
        with patch("apps.intranet.client.consultar") as consultar:
            consultar.side_effect = [
                [{"cadastrados": 6, "ativos": 0, "encerrados": 6}],
                [{"tipo_evento": "data", "total": 31}],
                [{"ganhador": "estagiario", "total": 4}],
                [{"dre": "DRE Itaquera", "total": 1}],
            ]
            bloco = handler.obter_ordem_inscricao(_JANELA, _JANELA_MES)

        chamadas = consultar.call_args_list
        assert chamadas[0].args == (queries.ORDEM_STATUS_GERAL,)
        assert chamadas[1].args == (queries.ORDEM_POR_TIPO, _JANELA)
        assert chamadas[2].args == (queries.ORDEM_POR_GANHADOR, _JANELA)
        assert chamadas[3].args == (queries.ORDEM_POR_DRE, _JANELA_MES)
        assert bloco["por_dre"] == [{"label": "DRE Itaquera", "value": 1}]
