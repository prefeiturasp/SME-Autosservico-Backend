"""Handlers dos dados do Rolê Agroecológico.

As inscrições são lidas uma vez (``obter_inscricoes``) e alimentam os três
blocos; cada bloco interpreta (``parser``) e monta o contrato (``mapper``).
"""

from datetime import datetime
from typing import Any

from apps.role_agroecologico import client
from apps.role_agroecologico import mapper
from apps.role_agroecologico import parser
from apps.role_agroecologico import queries
from apps.role_agroecologico.parser import Inscricao


def obter_inscricoes() -> list[Inscricao]:
    """Coleta e interpreta todas as inscrições (agendamentos)."""
    return parser.parse_inscricoes(client.consultar(queries.INSCRICOES))


def obter_participacao_logistica(
    inscricoes: list[Inscricao],
) -> dict[str, Any]:
    """Monta o bloco ``indicadores_participacao_logistica``."""
    return mapper.mapear_participacao_logistica(inscricoes)


def obter_unidades_produtivas(inscricoes: list[Inscricao]) -> dict[str, Any]:
    """Coleta as UPs e monta o bloco ``unidades_produtivas``."""
    ups = parser.parse_unidades_produtivas(
        client.consultar(queries.UNIDADES_PRODUTIVAS)
    )
    return mapper.mapear_unidades_produtivas(ups, inscricoes)


def obter_agendamentos_roles(
    inscricoes: list[Inscricao], agora: datetime
) -> dict[str, Any]:
    """Monta o bloco ``agendamentos_roles``."""
    return mapper.mapear_agendamentos_roles(inscricoes, agora)
