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
    acessos = parser.parse_acessos(
        client.consultar(queries.ACESSOS_UNICOS_HOJE)
    )
    por_tipo_perfil = parser.parse_por_tipo_perfil(
        client.consultar(queries.USUARIOS_POR_TIPO_PERFIL)
    )
    comparativo = parser.parse_comparativo_acessos(
        client.consultar(queries.COMPARATIVO_ACESSOS)
    )
    return mapper.mapear_usuarios(
        acesso_ativo,
        acessos,
        por_tipo_perfil,
        mapper.mapear_comparativo_acessos(comparativo),
    )


def obter_medicoes_iniciais() -> dict[str, Any]:
    """Coleta e monta o bloco ``medicoes_iniciais`` do contrato."""
    por_status = parser.parse_medicoes_por_status(
        client.consultar(queries.MEDICOES_INICIAIS_POR_STATUS)
    )
    return mapper.mapear_medicoes_iniciais(por_status)


def obter_produtos_homologados() -> dict[str, Any]:
    """Coleta e monta o bloco ``produtos_homologados`` do contrato."""
    dados = parser.parse_produtos_homologados(
        client.consultar(queries.PRODUTOS_HOMOLOGADOS)
    )
    return mapper.mapear_produtos_homologados(dados)


def obter_empresas_terceirizadas() -> dict[str, Any]:
    """Coleta e monta o bloco ``empresas_terceirizadas`` do contrato."""
    dados = parser.parse_empresas_terceirizadas(
        client.consultar(queries.EMPRESAS_TERCEIRIZADAS)
    )
    return mapper.mapear_empresas_terceirizadas(dados)


def obter_solicitacoes_dietas_especiais() -> dict[str, Any]:
    """Coleta e monta o bloco ``solicitacoes_dietas_especiais``."""
    por_periodo = parser.parse_solicitacoes_por_periodo(
        client.consultar(queries.SOLICITACOES_DIETAS_ESPECIAIS)
    )
    return mapper.mapear_solicitacoes(por_periodo)


def obter_solicitacoes_alimentacoes() -> dict[str, Any]:
    """Coleta e monta o bloco ``solicitacoes_alimentacoes``."""
    por_periodo = parser.parse_solicitacoes_por_periodo(
        client.consultar(queries.SOLICITACOES_ALIMENTACOES)
    )
    return mapper.mapear_solicitacoes(por_periodo)


def obter_cronogramas_entregas() -> dict[str, Any]:
    """Coleta o bloco ``cronogramas_entregas`` da logística."""
    return parser.parse_cronogramas_entregas(
        client.consultar(queries.CRONOGRAMAS_ENTREGAS)
    )


def obter_fichas_tecnicas_produtos() -> dict[str, Any]:
    """Coleta o bloco ``fichas_tecnicas_produtos`` da logística."""
    return parser.parse_fichas_tecnicas_produtos(
        client.consultar(queries.FICHAS_TECNICAS_PRODUTOS)
    )


def obter_layouts_embalagens() -> dict[str, Any]:
    """Coleta o bloco ``layouts_embalagens`` da logística."""
    return parser.parse_layouts_embalagens(
        client.consultar(queries.LAYOUTS_EMBALAGENS)
    )


def obter_fornecedores_distribuidores() -> dict[str, Any]:
    """Coleta o bloco ``fornecedores_distribuidores`` da logística."""
    return parser.parse_fornecedores_distribuidores(
        client.consultar(queries.FORNECEDORES_DISTRIBUIDORES)
    )
