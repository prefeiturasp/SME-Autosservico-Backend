"""Testes do bloco de medições iniciais do SIGPAE."""

from unittest.mock import patch

from apps.sigpae import handler
from apps.sigpae import mapper
from apps.sigpae import parser


class TestParserMedicoes:
    """Cobre a interpretação das linhas de status."""

    def test_agrupa_status_e_total(self) -> None:
        """As linhas viram um dicionário ``status -> total``."""
        linhas = [
            {"status": "MEDICAO_ENVIADA_PELA_UE", "total": 7},
            {"status": "MEDICAO_APROVADA_PELA_CODAE", "total": 3},
        ]

        assert parser.parse_medicoes_por_status(linhas) == {
            "MEDICAO_ENVIADA_PELA_UE": 7,
            "MEDICAO_APROVADA_PELA_CODAE": 3,
        }


class TestMapperMedicoes:
    """Cobre a montagem do bloco de medições iniciais."""

    def test_status_viram_as_cinco_categorias(self) -> None:
        """Os status do workflow são somados nas 5 categorias do painel."""
        por_status = {
            "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE": 10,
            "MEDICAO_CORRECAO_SOLICITADA": 2,
            "MEDICAO_ENVIADA_PELA_UE": 5,
            "MEDICAO_APROVADA_PELA_DRE": 4,
            "MEDICAO_CORRIGIDA_PARA_CODAE": 1,
            "MEDICAO_APROVADA_PELA_CODAE": 8,
        }

        assert mapper.mapear_medicoes_iniciais(por_status) == {
            "aguardando_envio_ue": 12,
            "enviadas_pelas_unidades": 5,
            "aprovadas_pelas_dres": 4,
            "aguardando_codae": 1,
            "aprovadas_codae": 8,
        }

    def test_status_ausente_conta_zero(self) -> None:
        """Categorias sem status correspondente ficam zeradas."""
        bloco = mapper.mapear_medicoes_iniciais(
            {"MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE": 16}
        )

        assert bloco["aguardando_envio_ue"] == 16
        assert bloco["aprovadas_codae"] == 0


class TestHandlerMedicoes:
    """Cobre o handler de medições iniciais."""

    def test_consulta_e_mapeia(self) -> None:
        """O handler consulta os status e devolve as categorias mapeadas."""
        with patch("apps.sigpae.client.consultar") as consultar:
            consultar.return_value = [
                {
                    "status": "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                    "total": 16,
                }
            ]
            bloco = handler.obter_medicoes_iniciais()

        assert bloco["aguardando_envio_ue"] == 16
