"""Handlers dos dados do SIGPAE."""

from typing import Any

from apps.sigpae import client
from apps.sigpae import mapper
from apps.sigpae import parser
from apps.sigpae import queries


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato."""
    acesso_ativo = parser.parse_acesso_ativo(
        client.consultar(queries.USUARIOS_ACESSO_ATIVO)
    )
    por_tipo_perfil = parser.parse_por_tipo_perfil(
        client.consultar(queries.USUARIOS_POR_TIPO_PERFIL)
    )
    return mapper.mapear_usuarios(acesso_ativo, por_tipo_perfil)


def obter_medicoes_iniciais() -> dict[str, Any]:
    """Monta o bloco ``medicoes_iniciais`` do contrato."""
    return mapper.mapear_medicoes_iniciais()
