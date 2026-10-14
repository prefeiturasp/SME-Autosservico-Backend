"""Testes do bloco de solicitações de dietas especiais do SIGPAE."""

from unittest.mock import patch

from apps.sigpae import handler
from apps.sigpae import mapper
from apps.sigpae import parser

_CAMPOS = ("total", "autorizadas", "aguardando", "negadas", "canceladas")
_ZEROS = dict.fromkeys(_CAMPOS, 0)


class TestParserSolicitacoes:
    """Cobre a interpretação das solicitações por período."""

    def test_sem_linhas_preenche_os_4_periodos_com_zeros(self) -> None:
        """Sem linhas, todos os períodos voltam zerados."""
        resultado = parser.parse_solicitacoes_por_periodo([])

        assert set(resultado) == {"dia", "quinzena", "mes", "trimestre"}
        assert all(periodo == _ZEROS for periodo in resultado.values())

    def test_periodo_ausente_vira_zeros(self) -> None:
        """Períodos que não voltam do banco recebem zeros."""
        linhas = [
            {
                "periodo": "dia",
                "total": 5,
                "autorizadas": 2,
                "aguardando": 3,
                "negadas": 0,
                "canceladas": 0,
            }
        ]

        resultado = parser.parse_solicitacoes_por_periodo(linhas)

        assert resultado["dia"]["total"] == 5
        assert resultado["mes"] == _ZEROS


class TestMapperSolicitacoes:
    """Cobre a montagem do bloco de solicitações."""

    def test_preserva_os_5_status_por_periodo(self) -> None:
        """O mapper mantém total e os quatro status em cada período."""
        por_periodo = {
            "dia": _ZEROS,
            "quinzena": {
                "total": 5,
                "autorizadas": 2,
                "aguardando": 3,
                "negadas": 0,
                "canceladas": 0,
            },
            "mes": _ZEROS,
            "trimestre": _ZEROS,
        }

        assert mapper.mapear_solicitacoes(por_periodo) == por_periodo


class TestHandlerDietas:
    """Cobre o handler de dietas especiais."""

    def test_consulta_e_mapeia(self) -> None:
        """O handler consulta as linhas por período e monta o bloco."""
        linhas = [
            {
                "periodo": "quinzena",
                "total": 5,
                "autorizadas": 2,
                "aguardando": 3,
                "negadas": 0,
                "canceladas": 0,
            }
        ]

        with patch("apps.sigpae.client.consultar", return_value=linhas):
            bloco = handler.obter_solicitacoes_dietas_especiais()

        assert bloco["quinzena"]["autorizadas"] == 2
        assert bloco["dia"] == _ZEROS
