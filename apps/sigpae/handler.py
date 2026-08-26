"""Handler dos dados de usuários do SIGPAE.

Orquestra o fluxo de aquisição: dispara as queries no banco, delega a
interpretação ao parser e a transformação ao mapper.
"""

from typing import Any

from apps.sigpae import client
from apps.sigpae import mapper
from apps.sigpae import parser
from apps.sigpae import queries


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato.

    Returns:
        Bloco ``usuarios`` no formato do contrato de entrega.
    """
    acesso_ativo = parser.parse_acesso_ativo(
        client.consultar(queries.USUARIOS_ACESSO_ATIVO)
    )
    por_tipo_perfil = parser.parse_por_tipo_perfil(
        client.consultar(queries.USUARIOS_POR_TIPO_PERFIL)
    )
    return mapper.mapear_usuarios(acesso_ativo, por_tipo_perfil)
