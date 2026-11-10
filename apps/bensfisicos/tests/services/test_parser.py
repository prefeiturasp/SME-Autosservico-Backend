"""Testes do parser dos dados do Bens Físicos."""

from decimal import Decimal
from typing import Any

from apps.bensfisicos import parser


class TestParser:
    def test_parse_inteiros_nulo_e_vazio_viram_zero(self) -> None:
        assert parser.parse_inteiros([], ("a",)) == {"a": 0}
        assert parser.parse_inteiros([{"a": None}], ("a",)) == {"a": 0}
        assert parser.parse_inteiros([{"a": 7}], ("a",)) == {"a": 7}

    def test_parse_decimal_converte_para_float(self) -> None:
        valor = parser.parse_decimal([{"m": Decimal("0.3")}], "m")

        assert valor == 0.3
        assert type(valor) is float
        assert parser.parse_decimal([{"m": None}], "m") == 0.0
        assert parser.parse_decimal([], "m") == 0.0

    def test_parse_por_unidade(self) -> None:
        linhas: list[dict[str, Any]] = [
            {
                "sigla": "PMSP/SME/SME-GAB/SMECOTIC",
                "nome": "COTIC",
                "bens": Decimal(493),
            },
            {"sigla": None, "nome": "Sem sigla", "bens": 2},
        ]

        unidades = parser.parse_por_unidade(linhas)

        assert unidades == [
            {
                "sigla": "PMSP/SME/SME-GAB/SMECOTIC",
                "nome": "COTIC",
                "bens": 493,
            },
            {"sigla": None, "nome": "Sem sigla", "bens": 2},
        ]
        assert type(unidades[0]["bens"]) is int
