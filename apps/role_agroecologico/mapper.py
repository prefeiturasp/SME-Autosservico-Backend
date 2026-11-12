"""Mapper dos dados do Rolê Agroecológico para o contrato de entrega ao BFF.

"Participaram" conta só a presença nas vivências realizadas; "inscritos"
conta todo mundo das inscrições não canceladas.
"""

from collections.abc import Iterable
from datetime import datetime
from datetime import timedelta
from typing import Any

from apps.role_agroecologico.parser import Inscricao
from apps.role_agroecologico.parser import UnidadeProdutiva
from apps.role_agroecologico.parser import presente

NAO_INFORMADO = "Não informado"

REALIZADO = "realizado"
CANCELADOS = frozenset({"cancelado", "solicitacao-cancelamento"})

_JANELA = timedelta(days=7)


def _realizadas(inscricoes: list[Inscricao]) -> list[Inscricao]:
    """Inscrições com a vivência realizada."""
    return [i for i in inscricoes if i.status == REALIZADO]


def _presentes(pessoas: Iterable[dict[str, Any]]) -> int:
    """Quantas pessoas da lista estão presentes."""
    return sum(1 for pessoa in pessoas if presente(pessoa))


def _itens(contagens: dict[str, int]) -> list[dict[str, Any]]:
    """``rótulo -> total`` em itens ``{label, value}``, desc."""
    return [
        {"label": label, "value": value}
        for label, value in sorted(
            contagens.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def _percentual(valor: int, total: int) -> float | None:
    """Percentual com uma casa; sem total, não há percentual."""
    return round(valor / total * 100, 1) if total else None


def mapear_participacao_logistica(
    inscricoes: list[Inscricao],
) -> dict[str, Any]:
    """Monta o bloco ``indicadores_participacao_logistica``.

    "Kits distribuídos" fica nulo: o autofornecimento pela própria UP, que
    é o caso comum, não é registrado no site.
    """
    realizadas = _realizadas(inscricoes)
    com_refeicao = [i for i in realizadas if i.oferta_almoco]
    estudantes = sum(_presentes(i.alunos) for i in realizadas)
    educadores = sum(_presentes(i.educadores) for i in realizadas)
    acompanhantes = sum(_presentes(i.acompanhantes) for i in realizadas)

    ues_por_dre: dict[str, set[str]] = {}
    for inscricao in inscricoes:
        if inscricao.codigo_eol_ue:
            ues_por_dre.setdefault(inscricao.dre or NAO_INFORMADO, set()).add(
                inscricao.codigo_eol_ue
            )

    return {
        "vivencias_realizadas": len(realizadas),
        "estudantes_participantes": estudantes,
        "estudantes_inscritos": sum(
            len(i.alunos) for i in inscricoes if i.status not in CANCELADOS
        ),
        "participantes_vivencias": estudantes + educadores + acompanhantes,
        "educadores_participantes": educadores,
        "refeicoes_estudantes": sum(
            _presentes(i.alunos) for i in com_refeicao
        ),
        "kits_distribuidos": None,
        "vivencias_com_refeicao": {
            "valor": len(com_refeicao),
            "total_realizadas": len(realizadas),
            "progresso_percentual": _percentual(
                len(com_refeicao), len(realizadas)
            ),
        },
        "ues_participantes_por_dre": _itens(
            {dre: len(ues) for dre, ues in ues_por_dre.items()}
        ),
    }


def mapear_unidades_produtivas(
    ups: list[UnidadeProdutiva], inscricoes: list[Inscricao]
) -> dict[str, Any]:
    """Monta o bloco ``unidades_produtivas``.

    UP visitada = UP de um roteiro com vivência realizada. "Perfil dos
    responsáveis" fica nulo: a UP é um CNPJ, sem pessoa física associada.
    """
    visitadas_ids: frozenset[int] = frozenset().union(
        *(i.ids_ups for i in _realizadas(inscricoes))
    )
    visitadas = sorted(
        (up.nome for up in ups if up.id in visitadas_ids), key=str.casefold
    )
    return {
        "ups_cadastradas": len(ups),
        "ups_preservacao_ambiental_manancial": sum(
            1 for up in ups if up.preservacao
        ),
        "ups_que_receberam_visita": len(visitadas),
        "lista_ups_que_receberam_visita": visitadas,
        "perfil_responsaveis_ups": None,
    }


def mapear_agendamentos_roles(
    inscricoes: list[Inscricao], agora: datetime
) -> dict[str, Any]:
    """Monta o bloco ``agendamentos_roles``.

    ``agora`` é a hora local sem fuso, como o WordPress grava ``post_date``.
    """
    hoje = agora.date()
    por_dre: dict[str, int] = {}
    for inscricao in inscricoes:
        dre = inscricao.dre or NAO_INFORMADO
        por_dre[dre] = por_dre.get(dre, 0) + 1

    return {
        "agendamentos_totais": len(inscricoes),
        "agendamentos_ultima_semana": sum(
            1 for i in inscricoes if i.criada_em >= agora - _JANELA
        ),
        "roles_concluidos": len(_realizadas(inscricoes)),
        "roles_previstos_semana": sum(
            1
            for i in inscricoes
            if i.status not in CANCELADOS
            and i.data_reservada is not None
            and hoje <= i.data_reservada <= hoje + _JANELA
        ),
        "agendamentos_por_dre": _itens(por_dre),
    }
