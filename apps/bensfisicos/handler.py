"""Handlers dos dados do Bens Físicos.

Cada função consulta o banco (``client``), interpreta as linhas
(``parser``) e monta o bloco do contrato (``mapper``).
"""

from typing import Any

from apps.bensfisicos import client
from apps.bensfisicos import mapper
from apps.bensfisicos import parser
from apps.bensfisicos import queries


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato."""
    ativos = parser.parse_inteiros(
        client.consultar(queries.USUARIOS_ATIVOS), ("com_acesso_ativo",)
    )["com_acesso_ativo"]
    unicos = client.consultar(queries.USUARIOS_UNICOS)
    return mapper.mapear_usuarios(
        ativos,
        parser.parse_inteiros(unicos, ("unicos_hoje",))["unicos_hoje"],
        parser.parse_decimal(unicos, "media_diaria_30_dias"),
    )


def obter_cadastro_de_bens() -> dict[str, Any]:
    """Coleta e monta o bloco ``cadastro_de_bens`` do contrato."""
    return mapper.mapear_cadastro(
        parser.parse_inteiros(
            client.consultar(queries.BENS),
            ("bens_cadastrados", "aguardando_aprovacao"),
        ),
        parser.parse_por_unidade(client.consultar(queries.BENS_POR_UNIDADE)),
    )


def obter_baixas_fisicas() -> dict[str, int]:
    """Coleta e monta o bloco ``baixas_fisicas`` do contrato."""
    return mapper.mapear_baixas(
        parser.parse_inteiros(
            client.consultar(queries.BAIXAS_FISICAS),
            ("aprovadas", "aguardando_aprovacao"),
        )
    )


def obter_movimentacoes() -> dict[str, int]:
    """Coleta e monta o bloco ``movimentacoes`` do contrato."""
    return mapper.mapear_movimentacoes(
        parser.parse_inteiros(
            client.consultar(queries.MOVIMENTACOES),
            ("realizadas", "pendentes"),
        ),
        parser.parse_inteiros(
            client.consultar(queries.TRANSFERENCIAS),
            ("transferencias_realizadas",),
        )["transferencias_realizadas"],
    )
