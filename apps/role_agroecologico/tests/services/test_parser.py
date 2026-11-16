"""Testes do parser do Rolê: desserialização do PHP e linhas do banco."""

import logging
from datetime import date
from typing import Any

import pytest

from apps.role_agroecologico import parser
from apps.role_agroecologico.tests.conftest import AUSENTE
from apps.role_agroecologico.tests.conftest import PRESENTE
from apps.role_agroecologico.tests.conftest import inscricao
from apps.role_agroecologico.tests.conftest import php
from apps.role_agroecologico.tests.conftest import turmas


class TestDesserializar:
    def test_arrays_viram_listas_e_acentos_sao_preservados(self) -> None:
        valor = php([{"nome": "João", "itens": ["a", "b"]}])

        assert parser.desserializar(valor, post_id=1, campo="x") == [
            {"nome": "João", "itens": ["a", "b"]}
        ]

    @pytest.mark.parametrize("valor", [None, ""])
    def test_vazio_vira_lista_vazia(self, valor: str | None) -> None:
        assert parser.desserializar(valor, post_id=1, campo="x") == []

    def test_valor_invalido_vira_lista_vazia_com_aviso(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING):
            resultado = parser.desserializar(
                "nao-serializado", post_id=7, campo="dados_turmas"
            )

        assert resultado == []
        assert "dados_turmas do post 7" in caplog.text


class TestPresente:
    @pytest.mark.parametrize(
        "marcacao", [True, 1, "1", "true", " TRUE ", None, "sim"]
    )
    def test_presente(self, marcacao: Any) -> None:
        assert parser.presente({"confirmacaoPresenca": marcacao})

    @pytest.mark.parametrize(
        "marcacao", [False, 0, "", "0", "false", " False ", []]
    )
    def test_ausente(self, marcacao: Any) -> None:
        assert not parser.presente({"confirmacaoPresenca": marcacao})

    def test_sem_marcacao_conta_como_presente(self) -> None:
        assert parser.presente({"nome": "Ana"})


class TestParseInscricoes:
    def test_interpreta_campos_serializados(self) -> None:
        [resultado] = parser.parse_inscricoes(
            [
                inscricao(
                    id="10",
                    status=" realizado ",
                    dados_turmas=turmas([PRESENTE, AUSENTE], [PRESENTE]),
                    dados_educadores=php([PRESENTE]),
                    dados_acompanhantes=php([AUSENTE]),
                    oferta_almoco="1",
                    ids_up_roteiro=php(["692", "abc", 691]),
                )
            ]
        )

        assert resultado.id == 10
        assert resultado.status == "realizado"
        assert resultado.alunos == [PRESENTE, AUSENTE, PRESENTE]
        assert resultado.educadores == [PRESENTE]
        assert resultado.acompanhantes == [AUSENTE]
        assert resultado.oferta_almoco is True
        assert resultado.ids_ups == frozenset({692, 691})

    def test_estruturas_inesperadas_sao_ignoradas(self) -> None:
        [resultado] = parser.parse_inscricoes(
            [
                inscricao(
                    status=None,
                    dados_turmas=php(
                        [{"nomeTurma": "Sem alunos"}, "lixo", {"x": 1}]
                    ),
                    dados_educadores=php({"rf": "123"}),
                    dados_acompanhantes=php(["lixo", PRESENTE]),
                    ids_up_roteiro=php("692"),
                )
            ]
        )

        assert resultado.status == ""
        assert resultado.alunos == []
        assert resultado.educadores == []
        assert resultado.acompanhantes == [PRESENTE]
        assert resultado.ids_ups == frozenset()
        assert resultado.oferta_almoco is False

    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            ("20251031", date(2025, 10, 31)),
            ("2025-12-23", date(2025, 12, 23)),
            ("31/10/2025", None),
            ("", None),
            (None, None),
        ],
    )
    def test_data_reservada_em_dois_formatos(
        self, valor: str | None, esperado: date | None
    ) -> None:
        [resultado] = parser.parse_inscricoes(
            [inscricao(data_reservada=valor)]
        )

        assert resultado.data_reservada == esperado

    @pytest.mark.parametrize("valor", ["", "   ", None])
    def test_dre_e_ue_vazias_viram_none(self, valor: str | None) -> None:
        [resultado] = parser.parse_inscricoes(
            [inscricao(dre=valor, codigo_eol_ue=valor)]
        )

        assert resultado.dre is None
        assert resultado.codigo_eol_ue is None


class TestParseUnidadesProdutivas:
    def test_interpreta_linhas(self) -> None:
        resultado = parser.parse_unidades_produtivas(
            [
                {"id": "690", "nome": " Sítio ", "preservacao": 1},
                {"id": 691, "nome": None, "preservacao": 0},
            ]
        )

        assert resultado == [
            parser.UnidadeProdutiva(id=690, nome="Sítio", preservacao=True),
            parser.UnidadeProdutiva(id=691, nome="", preservacao=False),
        ]
