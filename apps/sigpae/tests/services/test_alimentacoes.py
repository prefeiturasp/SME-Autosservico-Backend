"""Testes do bloco de solicitações de alimentações do SIGPAE."""

from unittest.mock import patch

from apps.sigpae import handler
from apps.sigpae import queries

_ZEROS = dict.fromkeys(
    ("total", "autorizadas", "aguardando", "negadas", "canceladas"), 0
)


class TestQueryAlimentacoes:
    """Cobre a composição da consulta de alimentações."""

    def test_une_kit_lanche_pela_onetoone(self) -> None:
        """Kit lanche entra via JOIN em kit_lanche_solicitacaokitlanche."""
        assert (
            "join kit_lanche_solicitacaokitlanche s"
            in queries.SOLICITACOES_ALIMENTACOES
        )
        assert (
            "kit_lanche_solicitacaokitlancheavulsa"
            in queries.SOLICITACOES_ALIMENTACOES
        )

    def test_total_ignora_rascunho(self) -> None:
        """Rascunho não conta como solicitação enviada."""
        assert (
            "count(*) filter (where status <> 'RASCUNHO') as total"
            in queries.SOLICITACOES_ALIMENTACOES
        )

    def test_informado_conta_como_autorizada(self) -> None:
        """Informativos (suspensão/inversão) terminam em INFORMADO."""
        assert "'INFORMADO'" in queries.SOLICITACOES_ALIMENTACOES


class TestHandlerAlimentacoes:
    """Cobre o handler de alimentações."""

    def test_consulta_e_mapeia(self) -> None:
        """O handler consulta as linhas por período e monta o bloco."""
        linhas = [
            {
                "periodo": "quinzena",
                "total": 19,
                "autorizadas": 10,
                "aguardando": 0,
                "negadas": 9,
                "canceladas": 0,
            }
        ]

        with patch("apps.sigpae.client.consultar", return_value=linhas):
            bloco = handler.obter_solicitacoes_alimentacoes()

        assert bloco["quinzena"]["negadas"] == 9
        assert bloco["dia"] == _ZEROS
