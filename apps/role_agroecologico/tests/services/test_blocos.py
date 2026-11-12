"""Testes dos blocos do contrato do Rolê, do banco ao mapper."""

from apps.role_agroecologico import handler
from apps.role_agroecologico import mapper
from apps.role_agroecologico import parser
from apps.role_agroecologico.tests.conftest import AGORA
from apps.role_agroecologico.tests.conftest import Banco
from apps.role_agroecologico.tests.conftest import inscricao


class TestParticipacaoLogistica:
    def test_conta_presenca_so_nas_realizadas(self, banco: Banco) -> None:
        bloco = handler.obter_participacao_logistica(
            handler.obter_inscricoes()
        )

        assert bloco == {
            "vivencias_realizadas": 2,
            "estudantes_participantes": 3,
            "estudantes_inscritos": 6,
            "participantes_vivencias": 5,
            "educadores_participantes": 1,
            "refeicoes_estudantes": 2,
            "kits_distribuidos": None,
            "vivencias_com_refeicao": {
                "valor": 1,
                "total_realizadas": 2,
                "progresso_percentual": 50.0,
            },
            "ues_participantes_por_dre": [
                {"label": "DRE Butantã", "value": 1},
                {"label": "DRE Penha", "value": 1},
                {"label": "Não informado", "value": 1},
            ],
        }

    def test_sem_realizadas_nao_ha_percentual(self) -> None:
        inscricoes = parser.parse_inscricoes([inscricao(codigo_eol_ue="")])

        bloco = mapper.mapear_participacao_logistica(inscricoes)

        assert bloco["vivencias_com_refeicao"] == {
            "valor": 0,
            "total_realizadas": 0,
            "progresso_percentual": None,
        }
        assert bloco["ues_participantes_por_dre"] == []


class TestUnidadesProdutivas:
    def test_cruza_ups_dos_roteiros_realizados(self, banco: Banco) -> None:
        bloco = handler.obter_unidades_produtivas(handler.obter_inscricoes())

        # A UP 999 não está publicada e a 690 é de inscrição não realizada.
        assert bloco == {
            "ups_cadastradas": 3,
            "ups_preservacao_ambiental_manancial": 2,
            "ups_que_receberam_visita": 2,
            "lista_ups_que_receberam_visita": ["Fazenda Vale", "horta Jardim"],
            "perfil_responsaveis_ups": None,
        }

    def test_sem_realizadas_nenhuma_up_visitada(self) -> None:
        bloco = mapper.mapear_unidades_produtivas([], [])

        assert bloco["ups_que_receberam_visita"] == 0
        assert bloco["lista_ups_que_receberam_visita"] == []


class TestAgendamentosRoles:
    def test_contagens_e_por_dre(self, banco: Banco) -> None:
        bloco = handler.obter_agendamentos_roles(
            handler.obter_inscricoes(), AGORA
        )

        assert bloco == {
            "agendamentos_totais": 4,
            "agendamentos_ultima_semana": 1,
            "roles_concluidos": 2,
            "roles_previstos_semana": 1,
            "agendamentos_por_dre": [
                {"label": "DRE Butantã", "value": 2},
                {"label": "DRE Penha", "value": 1},
                {"label": "Não informado", "value": 1},
            ],
        }

    def test_janela_da_semana_inclui_as_pontas(self) -> None:
        inscricoes = parser.parse_inscricoes(
            [
                inscricao(data_reservada="20261110"),
                inscricao(data_reservada="20261117"),
                inscricao(data_reservada="20261118"),
                inscricao(data_reservada="20261109"),
            ]
        )

        bloco = mapper.mapear_agendamentos_roles(inscricoes, AGORA)

        assert bloco["roles_previstos_semana"] == 2
