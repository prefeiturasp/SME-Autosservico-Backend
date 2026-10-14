"""Handlers dos dados do SIG-Escola.

Cada função consulta o banco (``client``), interpreta as linhas
(``parser``) e monta o bloco do contrato (``mapper``).
"""

from typing import Any

from apps.sigescola import client
from apps.sigescola import mapper
from apps.sigescola import parser
from apps.sigescola import queries

# Parâmetros das consultas recortadas: ``inicio`` e ``fim`` (date), ``dre``
# e ``ue`` (código EOL ou None). Ver ``queries``.
Filtro = dict[str, Any]


def obter_periodos() -> list[dict[str, Any]]:
    """Lista os períodos do PTRF, do mais recente para o mais antigo."""
    return parser.parse_periodos(client.consultar(queries.PERIODOS))


def obter_unidades(dre: str) -> list[dict[str, str]]:
    """Lista as UEs da DRE para o filtro da tela."""
    unidades = parser.parse_unidades(
        client.consultar(queries.UNIDADES_DA_DRE, {"dre": dre})
    )
    return mapper.mapear_unidades(unidades)


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato."""
    cadastro = client.consultar(queries.USUARIOS_ACESSO_ATIVO)
    return mapper.mapear_usuarios(
        parser.parse_inteiro(cadastro, "total"),
        parser.parse_inteiro(cadastro, "novos_30_dias"),
        parser.parse_logins(client.consultar(queries.USUARIOS_LOGINS)),
    )


def obter_plano_anual(filtro: Filtro) -> dict[str, int]:
    """Coleta e monta o bloco ``plano_anual_de_atividades``."""
    por_situacao = parser.parse_por_situacao(
        client.consultar(queries.PAA_POR_STATUS, filtro)
    )
    return mapper.mapear_plano_anual(por_situacao)


def obter_prestacao_de_contas(filtro: Filtro) -> dict[str, Any]:
    """Coleta e monta o bloco ``prestacao_de_contas``."""
    return mapper.mapear_prestacao_de_contas(
        ues_aptas=parser.parse_inteiro(
            client.consultar(queries.UES_APTAS, filtro), "total"
        ),
        por_situacao=parser.parse_por_situacao(
            client.consultar(queries.PRESTACOES_POR_STATUS, filtro)
        ),
        creditos=parser.parse_valor(
            client.consultar(queries.CREDITOS_DISPONIVEIS, filtro), "valor"
        ),
        despesas=parser.parse_valor(
            client.consultar(queries.DESPESAS_REGISTRADAS, filtro), "valor"
        ),
        demonstrativos=parser.parse_inteiro(
            client.consultar(queries.DEMONSTRATIVOS_GERADOS, filtro), "total"
        ),
        devolucao=parser.parse_valor(
            client.consultar(queries.DEVOLUCAO_AO_TESOURO, filtro), "valor"
        ),
    )


def obter_situacao_patrimonial(filtro: Filtro) -> dict[str, Any]:
    """Coleta e monta o bloco ``situacao_patrimonial``."""
    linhas = client.consultar(queries.BENS_PRODUZIDOS, filtro)
    return mapper.mapear_situacao_patrimonial(
        parser.parse_inteiro(linhas, "quantidade"),
        parser.parse_valor(linhas, "valor"),
    )
