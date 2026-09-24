"""Handlers dos dados do SGP."""

from typing import Any

from apps.sgp import client
from apps.sgp import mapper
from apps.sgp import parser
from apps.sgp import queries


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato."""
    acesso_ativo = parser.parse_acesso_ativo(
        client.consultar(queries.USUARIOS_ACESSO_ATIVO)
    )
    de_unidades = parser.parse_de_unidades(
        client.consultar(queries.USUARIOS_DE_UNIDADES)
    )
    return mapper.mapear_usuarios(acesso_ativo, de_unidades)


def obter_fechamento(ano_letivo: int, bimestre: int) -> dict[str, Any]:
    """Coleta e monta o bloco ``fechamento`` do contrato."""
    por_situacao = parser.parse_por_situacao(
        client.consultar(
            queries.FECHAMENTO_POR_SITUACAO, (ano_letivo, bimestre)
        )
    )
    return mapper.mapear_fechamento(por_situacao)


def obter_conselho_classe(ano_letivo: int, bimestre: int) -> dict[str, Any]:
    """Coleta e monta o bloco ``conselho_classe`` do contrato."""
    por_situacao = parser.parse_por_situacao(
        client.consultar(
            queries.CONSELHO_CLASSE_POR_SITUACAO, (ano_letivo, bimestre)
        )
    )
    alunos_ativos = parser.parse_escalar(
        client.consultar(queries.CONSELHO_CLASSE_ALUNOS_ATIVOS, (ano_letivo,)),
        "alunos_ativos",
    )
    return mapper.mapear_conselho_classe(por_situacao, alunos_ativos)


def obter_frequencias() -> dict[str, Any]:
    """Monta o bloco ``frequencias`` (deferido, indicadores nulos)."""
    return mapper.mapear_frequencias()


def obter_sondagens() -> dict[str, Any]:
    """Monta o bloco ``sondagens`` (deferido/nulo)."""
    return mapper.mapear_sondagens()
