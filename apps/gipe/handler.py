"""Handlers dos dados do GIPE.

Cada função consulta os bancos (``client``), interpreta as linhas
(``parser``) e monta o bloco do contrato (``mapper``). Como não há FK entre
o banco de ocorrências e o de usuários, os nomes de DRE, UE e analista são
buscados no banco de usuários e cruzados aqui.
"""

from collections.abc import Iterable
from datetime import date
from typing import Any

from apps.gipe import client
from apps.gipe import mapper
from apps.gipe import parser
from apps.gipe import queries

# Ano letivo: ``{"inicio": 1/jan, "fim": 1/jan do ano seguinte}``.
Janela = dict[str, date]


def _nomes_unidades(codigos: Iterable[str]) -> dict[str, str]:
    """Nomes das unidades (DRE ou UE) pelos códigos EOL."""
    lista = sorted({codigo for codigo in codigos if codigo})
    if not lista:
        return {}
    return parser.parse_nomes(
        client.consultar_usuarios(
            queries.UNIDADES_POR_CODIGO, {"codigos": lista}
        ),
        "codigo",
    )


def _nomes_analistas(usernames: Iterable[str]) -> dict[str, str]:
    """Nomes dos analistas pelo RF (username)."""
    lista = sorted(set(usernames))
    if not lista:
        return {}
    return parser.parse_nomes(
        client.consultar_usuarios(
            queries.NOMES_POR_USERNAME, {"usernames": lista}
        ),
        "username",
    )


def obter_kpis() -> dict[str, Any]:
    """Coleta e monta o bloco ``kpis`` do contrato."""
    dados = parser.parse_inteiros(
        client.consultar_usuarios(queries.KPIS_USUARIOS),
        ("com_acesso_ativo", "novos_30_dias", "unicos_hoje"),
    )
    return mapper.mapear_kpis(dados)


def obter_movimentacoes(janela: Janela) -> dict[str, Any]:
    """Coleta as movimentações do ano (usadas em dois blocos)."""
    linhas = client.consultar_ocorrencias(queries.MOVIMENTACOES, janela)
    return {
        **parser.parse_inteiros(linhas, ("ocorrencias", "encaminhamentos")),
        **parser.parse_dias(linhas, ("media_por_ocorrencia",)),
    }


def obter_ocorrencias(
    janela: Janela, movimentacoes: dict[str, Any]
) -> dict[str, Any]:
    """Coleta e monta o bloco ``ocorrencias`` do contrato."""
    por_dre = parser.parse_contagem(
        client.consultar_ocorrencias(queries.POR_DRE, janela)
    )
    por_ue = parser.parse_contagem(
        client.consultar_ocorrencias(queries.POR_UE, janela)
    )
    tratadas_por_dre = parser.parse_contagem(
        client.consultar_ocorrencias(queries.TRATADAS_POR_DRE, janela)
    )
    analistas = parser.parse_analistas(
        client.consultar_ocorrencias(queries.TRATADAS_POR_ANALISTA, janela)
    )
    return mapper.mapear_ocorrencias(
        status_geral=parser.parse_inteiros(
            client.consultar_ocorrencias(queries.STATUS_GERAL, janela),
            ("cadastrados", "abertas", "em_andamento", "finalizadas"),
        ),
        tempos=parser.parse_dias(
            client.consultar_ocorrencias(queries.TEMPO_RESPOSTA, janela),
            (
                "resolucao",
                "resolucao_30d",
                "resolucao_30d_anterior",
                "tratativa",
                "tratativa_30d",
                "tratativa_30d_anterior",
            ),
        ),
        sem_movimentacao_7_dias=parser.parse_inteiros(
            client.consultar_ocorrencias(queries.SEM_MOVIMENTACAO_7_DIAS),
            ("total",),
        )["total"],
        media_movimentacoes=movimentacoes["media_por_ocorrencia"],
        por_dre=por_dre,
        por_ue=por_ue,
        por_categoria=parser.parse_inteiros(
            client.consultar_ocorrencias(queries.POR_CATEGORIA, janela),
            ("patrimoniais", "interpessoais"),
        ),
        por_tipo=parser.parse_por_tipo(
            client.consultar_ocorrencias(queries.POR_TIPO, janela)
        ),
        por_mes=parser.parse_por_mes(
            client.consultar_ocorrencias(queries.POR_MES, janela)
        ),
        por_bimestre=parser.parse_por_bimestre(
            client.consultar_ocorrencias(queries.POR_BIMESTRE, janela)
        ),
        analistas=analistas,
        tratadas_por_dre=tratadas_por_dre,
        nomes_unidades=_nomes_unidades([*por_dre, *por_ue, *tratadas_por_dre]),
        nomes_analistas=_nomes_analistas(a["username"] for a in analistas),
    )


def obter_usuarios() -> dict[str, Any]:
    """Coleta e monta o bloco ``usuarios`` do contrato."""
    return mapper.mapear_usuarios(
        cadastrados=parser.parse_inteiros(
            client.consultar_usuarios(queries.KPIS_USUARIOS),
            ("cadastrados",),
        )["cadastrados"],
        perfis=parser.parse_perfis(
            client.consultar_usuarios(queries.USUARIOS_POR_PERFIL)
        ),
        por_dre=parser.parse_contagem_com_nome(
            client.consultar_usuarios(queries.USUARIOS_POR_DRE)
        ),
        por_ue=parser.parse_contagem_com_nome(
            client.consultar_usuarios(queries.USUARIOS_POR_UE)
        ),
    )


def obter_produtividade(movimentacoes: dict[str, Any]) -> dict[str, int]:
    """Coleta e monta o bloco ``produtividade`` do contrato."""
    anexos = parser.parse_inteiros(
        client.consultar_anexos(queries.ANEXOS_ENVIADOS), ("total",)
    )["total"]
    return mapper.mapear_produtividade(movimentacoes, anexos)
