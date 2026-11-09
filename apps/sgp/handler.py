"""Handlers dos dados do SGP."""

from typing import Any

from apps.sgp import client
from apps.sgp import mapper
from apps.sgp import parser
from apps.sgp import queries
from apps.sgp.periodo import Periodo


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato."""
    acesso_ativo = parser.parse_acesso_ativo(
        client.consultar(queries.USUARIOS_ACESSO_ATIVO)
    )
    de_unidades = parser.parse_de_unidades(
        client.consultar(queries.USUARIOS_DE_UNIDADES)
    )
    return mapper.mapear_usuarios(acesso_ativo, de_unidades)


def obter_fechamento(periodo: Periodo) -> dict[str, Any]:
    """Coleta e monta o bloco ``fechamento`` do contrato."""
    por_dre = parser.parse_por_dre_situacao(
        client.consultar(
            queries.FECHAMENTO_POR_DRE_SITUACAO,
            periodo.parametros(),
        )
    )
    return mapper.mapear_fechamento(por_dre)


def obter_conselho_classe(periodo: Periodo) -> dict[str, Any]:
    """Coleta e monta o bloco ``conselho_classe`` do contrato."""
    por_dre = parser.parse_por_dre_situacao(
        client.consultar(
            queries.CONSELHO_CLASSE_POR_DRE_SITUACAO,
            periodo.parametros(),
        )
    )
    previsto = parser.parse_previsto_por_dre(
        client.consultar(
            queries.CONSELHO_CLASSE_PREVISTO_POR_DRE,
            periodo.parametros(),
        )
    )
    return mapper.mapear_conselho_classe(por_dre, previsto)


def obter_periodos(ano_inicial: int, ano_final: int) -> list[dict[str, Any]]:
    """Coleta as opções do filtro de período."""
    periodos = parser.parse_periodos(
        client.consultar(
            queries.PERIODOS_CALENDARIO,
            {"ano_inicial": ano_inicial, "ano_final": ano_final},
        )
    )
    return mapper.mapear_periodos(periodos)


def obter_frequencias(ano_letivo: int, bimestre: int) -> dict[str, Any]:
    """Coleta e monta o bloco ``frequencias`` do contrato."""
    dados = parser.parse_frequencias(
        client.consultar(
            queries.FREQUENCIAS_LANCADAS_ESPERADAS, (ano_letivo, bimestre)
        )
    )
    return mapper.mapear_frequencias(dados)


def obter_sondagens(ano_letivo: int, bimestre: int) -> dict[str, Any]:
    """Coleta e monta o bloco ``sondagens`` do contrato."""
    dados = parser.parse_sondagens(
        client.consultar(
            queries.SONDAGENS_REALIZADAS_ESPERADAS, (ano_letivo, bimestre)
        )
    )
    return mapper.mapear_sondagens(dados)
