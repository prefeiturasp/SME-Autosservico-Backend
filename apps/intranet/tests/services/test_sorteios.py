"""Testes do bloco de Sorteios do Intranet (números do QA)."""

from decimal import Decimal
from typing import Any
from unittest.mock import patch

from apps.intranet import handler
from apps.intranet import mapper
from apps.intranet import parser
from apps.intranet import queries
from apps.intranet.handler import Janela

_JANELA_GERAL: Janela = {"inicio": None, "fim": None}


class TestParser:
    """Cobre a interpretação das linhas cruas de Sorteios."""

    def test_status_geral_converte_decimal(self) -> None:
        """``SUM`` do MySQL vem como ``Decimal`` e vira ``int``."""
        linhas = [
            {
                "cadastrados": 30,
                "realizados": Decimal(15),
                "ativos": Decimal(0),
                "encerrados": Decimal(15),
            }
        ]

        assert parser.parse_status_sorteios(linhas) == {
            "cadastrados": 30,
            "realizados": 15,
            "ativos": 0,
            "encerrados": 15,
        }

    def test_status_geral_sem_posts_retorna_zeros(self) -> None:
        """Sem posts, ``SUM`` vem nulo e os contadores zerados."""
        linhas = [
            {
                "cadastrados": 0,
                "realizados": None,
                "ativos": None,
                "encerrados": None,
            }
        ]

        assert parser.parse_status_sorteios(linhas)["realizados"] == 0

    def test_contagem_preserva_chave_nula(self) -> None:
        """Post sem ``tipo_evento`` chega ao mapper como chave ``None``."""
        linhas: list[dict[str, Any]] = [
            {"tipo_evento": "premio", "total": 13},
            {"tipo_evento": None, "total": 42},
        ]

        assert parser.parse_contagem_por_chave(linhas, "tipo_evento") == {
            "premio": 13,
            None: 42,
        }


class TestMapper:
    """Cobre a montagem dos cards de Sorteios."""

    def test_por_tipo_rotula_e_inclui_nao_informado(self) -> None:
        """Códigos viram rótulos; sem ``tipo_evento`` vira "Não informado"."""
        itens = mapper.mapear_por_tipo(
            {"premio": 13, "data": 7, "periodo": 4, None: 42}
        )

        assert itens == [
            {"label": "Não informado", "value": 42},
            {"label": "Premiação", "value": 13},
            {"label": "Data específica", "value": 7},
            {"label": "Período", "value": 4},
        ]
        assert sum(item["value"] for item in itens) == 66

    def test_por_tipo_completa_ausentes_e_omite_nao_informado(self) -> None:
        """Tipos ausentes viram zero; "Não informado" só se houver."""
        itens = mapper.mapear_por_tipo({"premio": 2})

        assert itens == [
            {"label": "Premiação", "value": 2},
            {"label": "Data específica", "value": 0},
            {"label": "Período", "value": 0},
        ]

    def test_por_tipo_valor_desconhecido_vai_para_nao_informado(self) -> None:
        """Valor de ``tipo_evento`` fora do enum soma em "Não informado"."""
        itens = mapper.mapear_por_tipo({"outro": 3, None: 1})

        assert {"label": "Não informado", "value": 4} in itens

    def test_por_ganhador_sempre_tres_grupos(self) -> None:
        """Parceiros aparece com zero mesmo sem caso no QA."""
        itens = mapper.mapear_por_ganhador({"servidor": 39, "estagiario": 27})

        assert itens == [
            {"label": "Servidores", "value": 39},
            {"label": "Estagiários", "value": 27},
            {"label": "Parceiros", "value": 0},
        ]

    def test_por_dre_mantem_valor_e_agrupa_vazios(self) -> None:
        """DRE vai como veio; vazio e nulo viram um só "Não informado"."""
        itens = mapper.mapear_por_dre(
            {"DRE Pirituba": 8, "DRE Santo Amaro": 9, "": 1, None: 2}
        )

        assert itens == [
            {"label": "DRE Santo Amaro", "value": 9},
            {"label": "DRE Pirituba", "value": 8},
            {"label": "Não informado", "value": 3},
        ]


class TestHandler:
    """Cobre a orquestração das consultas de Sorteios."""

    def test_orquestra_as_quatro_consultas(self) -> None:
        """Status sem janela; tipo/ganhador/DRE recebem a janela."""
        with patch("apps.intranet.client.consultar") as consultar:
            consultar.side_effect = [
                [
                    {
                        "cadastrados": 30,
                        "realizados": 15,
                        "ativos": 0,
                        "encerrados": 15,
                    }
                ],
                [{"tipo_evento": "premio", "total": 13}],
                [{"ganhador": "servidor", "total": 39}],
                [{"dre": "DRE Penha", "total": 5}],
            ]
            bloco = handler.obter_sorteios(_JANELA_GERAL)

        chamadas = consultar.call_args_list
        assert chamadas[0].args == (queries.SORTEIOS_STATUS_GERAL,)
        assert chamadas[1].args == (queries.SORTEIOS_POR_TIPO, _JANELA_GERAL)
        assert chamadas[2].args[0] == queries.SORTEIOS_POR_GANHADOR
        assert chamadas[3].args[0] == queries.SORTEIOS_POR_DRE
        assert bloco["status_geral"]["realizados"] == 15
        assert bloco["por_tipo"][0] == {"label": "Premiação", "value": 13}
        assert bloco["por_ganhador"][0] == {"label": "Servidores", "value": 39}
        assert bloco["por_dre"] == [{"label": "DRE Penha", "value": 5}]
