"""Testes do bloco de medições iniciais do SIGPAE."""

from apps.sigpae import handler
from apps.sigpae import mapper

_BLOCO_NULO = {
    "aguardando_envio_ue": None,
    "enviadas_pelas_unidades": None,
    "aprovadas_pelas_dres": None,
    "aguardando_codae": None,
    "aprovadas_codae": None,
}


class TestMapperMedicoes:
    """Cobre a montagem do bloco de medições iniciais."""

    def test_categorias_nulas_ate_definir_enum(self) -> None:
        """Enquanto o funil não é validado, as categorias são None."""
        assert mapper.mapear_medicoes_iniciais() == _BLOCO_NULO


class TestHandlerMedicoes:
    """Cobre o handler de medições iniciais."""

    def test_devolve_bloco_pendente_sem_consultar_banco(self) -> None:
        """O handler devolve o bloco nulo, sem tocar o banco."""
        assert handler.obter_medicoes_iniciais() == _BLOCO_NULO
