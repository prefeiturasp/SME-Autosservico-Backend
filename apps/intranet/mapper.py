"""Mapper dos dados do Intranet para o contrato de entrega ao BFF."""

from typing import Any

NAO_INFORMADO = "Não informado"

# Valores do campo ACF ``tipo_evento``.
_ROTULOS_TIPO = {
    "premio": "Premiação",
    "data": "Data específica",
    "periodo": "Período",
}

_ROTULOS_GANHADOR = {
    "servidor": "Servidores",
    "estagiario": "Estagiários",
    "parceiro": "Parceiros",
}


def _kpi(valor: int) -> dict[str, Any]:
    """KPI de usuário; sem histórico de login, a tendência é sempre null."""
    return {"valor": valor, "tendencia": None, "tendencia_label": None}


def _itens(contagens: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"label": label, "value": value}
        for label, value in sorted(
            contagens.items(), key=lambda item: item[1], reverse=True
        )
    ]


def mapear_kpis(dados: dict[str, int]) -> dict[str, Any]:
    """Monta o bloco ``kpis``."""
    return {
        "acesso_ativo": _kpi(dados["com_acesso_ativo"]),
        "usuarios_unicos": _kpi(dados["unicos_hoje"]),
        "acessos_hoje": _kpi(dados["unicos_hoje"]),
    }


def mapear_por_tipo(por_codigo: dict[str | None, int]) -> list[dict[str, Any]]:
    """Monta o card "por tipo".

    Os três tipos conhecidos sempre aparecem (zero quando ausentes); post
    sem ``tipo_evento`` (ou com valor desconhecido) vira "Não informado",
    que só aparece quando houver algum.
    """
    contagens = dict.fromkeys(_ROTULOS_TIPO.values(), 0)
    nao_informado = 0
    for codigo, total in por_codigo.items():
        rotulo = _ROTULOS_TIPO.get(codigo or "")
        if rotulo is None:
            nao_informado += total
        else:
            contagens[rotulo] += total
    if nao_informado:
        contagens[NAO_INFORMADO] = nao_informado
    return _itens(contagens)


def mapear_por_ganhador(
    por_codigo: dict[str | None, int],
) -> list[dict[str, Any]]:
    """Monta o card "por ganhador", com os três grupos sempre presentes."""
    return _itens(
        {
            rotulo: por_codigo.get(codigo, 0)
            for codigo, rotulo in _ROTULOS_GANHADOR.items()
        }
    )


def mapear_por_dre(por_dre: dict[str | None, int]) -> list[dict[str, Any]]:
    """Monta o card "por DRE", com o ``dre`` como veio do banco."""
    contagens: dict[str, int] = {}
    for dre, total in por_dre.items():
        rotulo = (dre or "").strip() or NAO_INFORMADO
        contagens[rotulo] = contagens.get(rotulo, 0) + total
    return _itens(contagens)


def mapear_sorteios(
    status_geral: dict[str, int],
    por_tipo: dict[str | None, int],
    por_ganhador: dict[str | None, int],
    por_dre: dict[str | None, int],
) -> dict[str, Any]:
    """Monta o bloco ``sorteios``."""
    return {
        "status_geral": {
            "cadastrados": status_geral["cadastrados"],
            "realizados": status_geral["realizados"],
            "ativos": status_geral["ativos"],
            "encerrados": status_geral["encerrados"],
        },
        "por_tipo": mapear_por_tipo(por_tipo),
        "por_ganhador": mapear_por_ganhador(por_ganhador),
        "por_dre": mapear_por_dre(por_dre),
    }


def mapear_ordem_inscricao(
    status_geral: dict[str, int],
    por_tipo: dict[str | None, int],
    por_ganhador: dict[str | None, int],
    por_dre: dict[str | None, int],
) -> dict[str, Any]:
    """Monta o bloco ``ordem_inscricao`` (sem "realizados")."""
    return {
        "status_geral": {
            "cadastrados": status_geral["cadastrados"],
            "ativos": status_geral["ativos"],
            "encerrados": status_geral["encerrados"],
        },
        "por_tipo": mapear_por_tipo(por_tipo),
        "por_ganhador": mapear_por_ganhador(por_ganhador),
        "por_dre": mapear_por_dre(por_dre),
    }


def mapear_oportunidades(dados: dict[str, int]) -> dict[str, int]:
    """Monta o bloco ``oportunidades``."""
    return {
        "cadastradas": dados["oportunidades_cadastradas"],
        "cvs_cadastrados": dados["cvs_cadastrados"],
        "inscricoes_realizadas": dados["inscricoes_realizadas"],
        "contratacoes_efetivadas": dados["contratacoes_efetivadas"],
    }
