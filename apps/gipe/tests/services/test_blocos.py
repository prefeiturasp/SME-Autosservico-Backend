"""Testes de parser, mapper e handler dos blocos do GIPE."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from apps.gipe import handler
from apps.gipe import mapper
from apps.gipe import parser
from apps.gipe import queries
from apps.gipe.tests.conftest import Bancos

_JANELA: handler.Janela = {
    "inicio": date(2026, 1, 1),
    "fim": date(2027, 1, 1),
}


class TestParser:
    def test_inteiros_sem_linhas_retorna_zeros(self) -> None:
        assert parser.parse_inteiros([], ("total",)) == {"total": 0}

    def test_dias_preserva_nulo_e_converte_decimal(self) -> None:
        linhas = [{"resolucao": Decimal("1.5"), "tratativa": None}]

        assert parser.parse_dias(linhas, ("resolucao", "tratativa")) == {
            "resolucao": 1.5,
            "tratativa": None,
        }

    def test_contagem_agrupa_codigo_nulo_em_vazio(self) -> None:
        linhas: list[dict[str, Any]] = [
            {"codigo": None, "total": 1},
            {"codigo": "", "total": 2},
            {"codigo": "108600", "total": 3},
        ]

        assert parser.parse_contagem(linhas) == {"": 3, "108600": 3}

    def test_nomes_ignora_nome_vazio(self) -> None:
        linhas = [
            {"username": "123", "nome": "Ana"},
            {"username": "456", "nome": ""},
        ]

        assert parser.parse_nomes(linhas, "username") == {"123": "Ana"}

    def test_por_tipo_separa_patrimonial_de_interpessoal(self) -> None:
        linhas = [
            {"patrimonial": True, "nome": "Furto", "total": 2},
            {"patrimonial": False, "nome": "Bullying", "total": 1},
        ]

        assert parser.parse_por_tipo(linhas) == {
            True: {"Furto": 2},
            False: {"Bullying": 1},
        }


class TestNomes:
    @pytest.mark.parametrize(
        ("nome", "esperado"),
        [
            ("DIRETORIA REGIONAL DE EDUCACAO IPIRANGA", "Ipiranga"),
            (
                "DIRETORIA REGIONAL DE EDUCAÇÃO CAPELA DO SOCORRO",
                "Capela do Socorro",
            ),
            (
                "DIRETORIA REGIONAL DE EDUCACAO FREGUESIA/BRASILANDIA",
                "Freguesia/Brasilandia",
            ),
            ("SAO MIGUEL", "Sao Miguel"),
        ],
    )
    def test_nome_curto_dre(self, nome: str, esperado: str) -> None:
        assert mapper.nome_curto_dre(nome) == esperado

    @pytest.mark.parametrize(
        ("cargo", "admin", "esperado"),
        [
            ("DIRETOR DE ESCOLA", False, "Diretor de Escola"),
            (
                "ASSISTENTE DE DIRETOR DE ESCOLA",
                False,
                "Assistente de direção",
            ),
            ("PONTO FOCAL DRE", True, "Ponto focal admin"),
            ("GIPE", True, "GIPE admin"),
            ("SUPERVISOR ESCOLAR", False, "Supervisor Escolar"),
        ],
    )
    def test_rotulo_perfil(
        self, cargo: str, admin: bool, esperado: str
    ) -> None:
        assert mapper.rotulo_perfil(cargo, admin) == esperado


class TestKpis:
    def test_acesso_ativo_com_novos_tem_tendencia(self) -> None:
        bloco = mapper.mapear_kpis(
            {"com_acesso_ativo": 7, "novos_30_dias": 1, "unicos_hoje": 3}
        )

        assert bloco["acesso_ativo"] == {
            "valor": 7,
            "tendencia": "above",
            "tendencia_label": "1 novo nos últimos 30 dias",
        }
        assert bloco["acessos_hoje"]["valor"] == 3
        assert bloco["usuarios_unicos"]["tendencia"] is None

    def test_plural_e_sem_novos(self) -> None:
        com_novos = mapper.mapear_kpis(
            {"com_acesso_ativo": 7, "novos_30_dias": 2, "unicos_hoje": 0}
        )
        sem_novos = mapper.mapear_kpis(
            {"com_acesso_ativo": 7, "novos_30_dias": 0, "unicos_hoje": 0}
        )

        assert com_novos["acesso_ativo"]["tendencia_label"] == (
            "2 novos nos últimos 30 dias"
        )
        assert sem_novos["acesso_ativo"]["tendencia"] is None

    def test_handler_le_do_banco_de_usuarios(self, bancos: Bancos) -> None:
        bloco = handler.obter_kpis()

        assert bloco["acesso_ativo"]["valor"] == 7
        assert bancos.consultas("usuarios", queries.KPIS_USUARIOS) == [()]


class TestTempoResposta:
    @pytest.mark.parametrize(
        ("atual", "anterior", "esperado"),
        [
            (2.0, 2.5, ("below", "20% mais rápido")),
            (3.0, 2.0, ("above", "50% mais lento")),
            (2.0, 2.0, (None, None)),
            (None, 2.0, (None, None)),
            (2.0, None, (None, None)),
            (2.0, 0.0, (None, None)),
        ],
    )
    def test_tendencia(
        self,
        atual: float | None,
        anterior: float | None,
        esperado: tuple[str | None, str | None],
    ) -> None:
        assert mapper.tendencia_tempo(atual, anterior) == esperado

    def test_sem_ocorrencia_finalizada_fica_nulo(self) -> None:
        bloco = mapper.mapear_tempo_resposta(
            dict.fromkeys(
                (
                    "resolucao",
                    "resolucao_30d",
                    "resolucao_30d_anterior",
                    "tratativa",
                    "tratativa_30d",
                    "tratativa_30d_anterior",
                )
            )
        )

        assert bloco["tempo_medio_resolucao_dias"] is None
        assert bloco["tendencia_primeira_tratativa"] is None


class TestSeries:
    def test_por_mes_rotula_e_marca_so_o_primeiro_pico(self) -> None:
        itens = mapper.mapear_por_mes(
            [
                (date(2026, 3, 1), 1),
                (date(2026, 4, 1), 3),
                (date(2026, 5, 1), 3),
            ]
        )

        assert itens == [
            {"label": "Março/26", "valor": 1, "pico": False},
            {"label": "Abril/26", "valor": 3, "pico": True},
            {"label": "Maio/26", "valor": 3, "pico": False},
        ]

    def test_por_mes_vazio(self) -> None:
        assert mapper.mapear_por_mes([]) == []

    def test_por_bimestre_em_ordem(self) -> None:
        assert mapper.mapear_por_bimestre({3: 1, 1: 2}) == [
            {"label": "1º Bimestre", "value": 2},
            {"label": "3º Bimestre", "value": 1},
        ]

    def test_analista_sem_nome_fica_com_rf(self) -> None:
        itens = mapper.mapear_analistas(
            [
                {
                    "username": "7210418",
                    "ocorrencias_tratadas": 1,
                    "tempo_medio_dias": 0.004,
                },
                {
                    "username": "123",
                    "ocorrencias_tratadas": 4,
                    "tempo_medio_dias": 2.46,
                },
            ],
            {"123": "Maria Souza"},
        )

        assert itens == [
            {
                "analista": "Maria Souza",
                "ocorrencias_tratadas": 4,
                "tempo_medio": "2,5 dias",
            },
            {
                "analista": "7210418",
                "ocorrencias_tratadas": 1,
                "tempo_medio": "0,0 dias",
            },
        ]


class TestOcorrencias:
    def test_monta_bloco_cruzando_os_dois_bancos(self, bancos: Bancos) -> None:
        movimentacoes = handler.obter_movimentacoes(_JANELA)
        bloco = handler.obter_ocorrencias(_JANELA, movimentacoes)

        assert bloco["status_geral"]["cadastrados"] == 2
        assert bloco["por_dre"] == [{"label": "Ipiranga", "value": 2}]
        assert bloco["por_unidade_educacional"] == [
            {"label": "EMEF PERICLES EUGENIO DA SILVA RAMOS", "value": 2}
        ]
        assert bloco["tratadas_por_dre"] == [{"label": "Ipiranga", "value": 1}]
        assert bloco["por_tipo_patrimonial"] == [
            {"label": "Furto", "value": 1}
        ]
        assert bloco["por_mes"] == [
            {"label": "Abril/26", "valor": 2, "pico": True}
        ]
        assert bloco["tratadas_por_analista"][0]["analista"] == "7210418"
        assert bloco["tempo_resposta"]["tempo_medio_resolucao_dias"] == (
            pytest.approx(0.004)
        )
        assert bloco["tempo_resposta"]["tendencia_resolucao"] == "below"
        assert bloco["prazos_movimentacoes"] == {
            "dentro_do_prazo": None,
            "fora_do_prazo": None,
            "sem_movimentacao_7_dias": 1,
            "media_movimentacoes_por_ocorrencia": pytest.approx(2.0),
        }

    def test_uma_consulta_de_nomes_com_todos_os_codigos(
        self, bancos: Bancos
    ) -> None:
        handler.obter_ocorrencias(
            _JANELA, handler.obter_movimentacoes(_JANELA)
        )

        assert bancos.consultas("usuarios", queries.UNIDADES_POR_CODIGO) == [
            {"codigos": ["019455", "108600"]}
        ]
        assert bancos.consultas("usuarios", queries.NOMES_POR_USERNAME) == [
            {"usernames": ["7210418"]}
        ]
        assert bancos.consultas("ocorrencias", queries.POR_DRE) == [_JANELA]
        assert bancos.consultas(
            "ocorrencias", queries.SEM_MOVIMENTACAO_7_DIAS
        ) == [()]

    def test_sem_ocorrencias_nao_consulta_nomes(self, bancos: Bancos) -> None:
        for query in (
            queries.POR_DRE,
            queries.POR_UE,
            queries.TRATADAS_POR_DRE,
            queries.TRATADAS_POR_ANALISTA,
        ):
            bancos.ocorrencias[query] = []

        bloco = handler.obter_ocorrencias(
            _JANELA, handler.obter_movimentacoes(_JANELA)
        )

        assert bloco["por_dre"] == []
        assert bancos.consultas("usuarios", queries.UNIDADES_POR_CODIGO) == []
        assert bancos.consultas("usuarios", queries.NOMES_POR_USERNAME) == []

    def test_codigo_sem_nome_ou_vazio(self, bancos: Bancos) -> None:
        bancos.ocorrencias[queries.POR_DRE] = [
            {"codigo": "999999", "total": 2},
            {"codigo": None, "total": 1},
        ]

        bloco = handler.obter_ocorrencias(
            _JANELA, handler.obter_movimentacoes(_JANELA)
        )

        assert bloco["por_dre"] == [
            {"label": "999999", "value": 2},
            {"label": "Não informado", "value": 1},
        ]

    def test_ano_sem_ocorrencias_media_nula(self, bancos: Bancos) -> None:
        bancos.ocorrencias[queries.MOVIMENTACOES] = [
            {
                "ocorrencias": 0,
                "encaminhamentos": 0,
                "media_por_ocorrencia": None,
            }
        ]

        movimentacoes = handler.obter_movimentacoes(_JANELA)
        bloco = handler.obter_ocorrencias(_JANELA, movimentacoes)

        assert (
            bloco["prazos_movimentacoes"]["media_movimentacoes_por_ocorrencia"]
            is None
        )


class TestUsuarios:
    def test_perfis_percentual_e_contagem_da_mesma_base(
        self, bancos: Bancos
    ) -> None:
        bloco = handler.obter_usuarios()

        assert bloco["cadastrados"] == 11
        assert bloco["perfis_mais_utilizados"] == [
            {"label": "Diretor de Escola", "value": 5},
            {"label": "GIPE", "value": 2},
            {"label": "GIPE admin", "value": 2},
            {"label": "Ponto focal", "value": 2},
        ]
        assert bloco["por_tipo_de_perfil"][0] == {
            "label": "Diretor de Escola",
            "percentage": 45,
        }
        assert bloco["por_dre"] == [{"label": "Ipiranga", "value": 5}]
        assert bloco["por_unidade_educacional"] == [
            {"label": "EMEF PERICLES EUGENIO DA SILVA RAMOS", "value": 5}
        ]

    def test_sem_usuarios_percentual_zero(self) -> None:
        bloco = mapper.mapear_usuarios(
            cadastrados=0, perfis=[], por_dre=[], por_ue=[]
        )

        assert bloco["por_tipo_de_perfil"] == []
        assert bloco["perfis_mais_utilizados"] == []

    def test_dre_sem_nome_fica_com_codigo(self) -> None:
        bloco = mapper.mapear_usuarios(
            cadastrados=1,
            perfis=[],
            por_dre=[{"codigo": "108600", "nome": None, "total": 1}],
            por_ue=[],
        )

        assert bloco["por_dre"] == [{"label": "108600", "value": 1}]


class TestProdutividade:
    def test_atualizacoes_somam_criacao_e_encaminhamentos(
        self, bancos: Bancos
    ) -> None:
        bloco = handler.obter_produtividade(
            handler.obter_movimentacoes(_JANELA)
        )

        assert bloco == {
            "encaminhamentos_realizados": 2,
            "anexos_enviados": 0,
            "atualizacoes_nas_ocorrencias": 4,
        }
        assert bancos.consultas("anexos", queries.ANEXOS_ENVIADOS) == [()]
