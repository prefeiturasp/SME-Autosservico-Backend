"""Handlers dos dados do Intranet."""

from datetime import datetime
from typing import Any

from apps.intranet import client
from apps.intranet import mapper
from apps.intranet import parser
from apps.intranet import queries

# Recorte de data das inscrições
Janela = dict[str, datetime | None]


def obter_kpis() -> dict[str, Any]:
    """Coleta e monta o bloco ``kpis`` do contrato."""
    dados = parser.parse_kpis(client.consultar(queries.KPIS_USUARIOS))
    return mapper.mapear_kpis(dados)


def obter_sorteios(janela: Janela) -> dict[str, Any]:
    """Coleta e monta o bloco ``sorteios`` do contrato."""
    status_geral = parser.parse_status_sorteios(
        client.consultar(queries.SORTEIOS_STATUS_GERAL)
    )
    por_tipo = parser.parse_contagem_por_chave(
        client.consultar(queries.SORTEIOS_POR_TIPO, janela), "tipo_evento"
    )
    por_ganhador = parser.parse_contagem_por_chave(
        client.consultar(queries.SORTEIOS_POR_GANHADOR, janela), "ganhador"
    )
    por_dre = parser.parse_contagem_por_chave(
        client.consultar(queries.SORTEIOS_POR_DRE, janela), "dre"
    )
    return mapper.mapear_sorteios(
        status_geral, por_tipo, por_ganhador, por_dre
    )


def obter_ordem_inscricao(
    janela: Janela, janela_mes: Janela
) -> dict[str, Any]:
    """Coleta e monta o bloco ``ordem_inscricao`` do contrato."""
    status_geral = parser.parse_status_ordem(
        client.consultar(queries.ORDEM_STATUS_GERAL)
    )
    por_tipo = parser.parse_contagem_por_chave(
        client.consultar(queries.ORDEM_POR_TIPO, janela), "tipo_evento"
    )
    por_ganhador = parser.parse_contagem_por_chave(
        client.consultar(queries.ORDEM_POR_GANHADOR, janela), "ganhador"
    )
    por_dre = parser.parse_contagem_por_chave(
        client.consultar(queries.ORDEM_POR_DRE, janela_mes), "dre"
    )
    return mapper.mapear_ordem_inscricao(
        status_geral, por_tipo, por_ganhador, por_dre
    )


def obter_oportunidades() -> dict[str, Any]:
    """Coleta e monta o bloco ``oportunidades`` do contrato."""
    dados = parser.parse_oportunidades(
        client.consultar(queries.OPORTUNIDADES_STATUS_GERAL)
    )
    return mapper.mapear_oportunidades(dados)
