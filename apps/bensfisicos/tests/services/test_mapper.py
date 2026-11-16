"""Testes do mapper do Bens Físicos para o contrato."""

import pytest

from apps.bensfisicos import mapper


class TestSiglaCurta:
    @pytest.mark.parametrize(
        ("sigla", "nome", "esperado"),
        [
            ("PMSP/SME/SME-GAB/SMECOTIC", "X", "SMECOTIC"),
            ("SPDM", "X", "SPDM"),
            ("PMSP/SME/", "X", "SME"),
            (" PMSP/SME/COPED ", "X", "COPED"),
            (None, "Unidade X", "Unidade X"),
            ("", "Unidade X", "Unidade X"),
            ("/", "Unidade X", "Unidade X"),
        ],
    )
    def test_ultimo_trecho_ou_nome(
        self, sigla: str | None, nome: str, esperado: str
    ) -> None:
        assert mapper.sigla_curta(sigla, nome) == esperado


class TestVariacaoPercentual:
    @pytest.mark.parametrize(
        ("hoje", "media", "esperado"),
        [(4, 2.0, 100.0), (1, 3.0, -66.7), (2, 2.0, 0.0), (3, 0.0, None)],
    )
    def test_variacao_sobre_a_media(
        self, hoje: int, media: float, esperado: float | None
    ) -> None:
        assert mapper.variacao_percentual(hoje, media) == esperado


class TestMapear:
    def test_mapear_usuarios(self) -> None:
        assert mapper.mapear_usuarios(6, 1, 0.3) == {
            "com_acesso_ativo": {"valor": 6},
            "unicos_por_dia": {
                "valor": 1,
                "variacao_percentual_30_dias": 233.3,
            },
        }

    def test_mapear_usuarios_sem_media_nao_tem_variacao(self) -> None:
        usuarios = mapper.mapear_usuarios(0, 0, 0.0)

        assert usuarios["unicos_por_dia"] == {
            "valor": 0,
            "variacao_percentual_30_dias": None,
        }

    def test_mapear_cadastro_ordena_por_bens_e_encurta_sigla(self) -> None:
        cadastro = mapper.mapear_cadastro(
            {"bens_cadastrados": 1171, "aguardando_aprovacao": 53},
            [
                {"sigla": "SPDM", "nome": "SPDM", "bens": 339},
                {"sigla": "PMSP/SME/ZETA", "nome": "Zeta", "bens": 339},
                {"sigla": "PMSP/SME/SMECOTIC", "nome": "COTIC", "bens": 493},
            ],
        )

        assert cadastro == {
            "bens_cadastrados": 1171,
            "aguardando_aprovacao": 53,
            "por_unidade_administrativa": [
                {"sigla": "SMECOTIC", "nome": "COTIC", "bens": 493},
                {"sigla": "SPDM", "nome": "SPDM", "bens": 339},
                {"sigla": "ZETA", "nome": "Zeta", "bens": 339},
            ],
        }

    def test_mapear_baixas(self) -> None:
        assert mapper.mapear_baixas(
            {"aprovadas": 42, "aguardando_aprovacao": 0}
        ) == {"aprovadas": 42, "aguardando_aprovacao": 0}

    def test_mapear_movimentacoes(self) -> None:
        assert mapper.mapear_movimentacoes(
            {"realizadas": 1461, "pendentes": 80}, 7
        ) == {
            "realizadas": 1461,
            "pendentes": 80,
            "transferencias_realizadas": 7,
        }
