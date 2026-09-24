"""Mapper dos dados do SGP para o contrato de entrega ao BFF."""

from typing import Any

# Enum SituacaoFechamento (0 e 1 são unidos em "não iniciados" na query).
_FECHAMENTO_BUCKETS = {
    0: "nao_iniciados",
    2: "processado_pendencias",
    3: "processado_sucesso",
    4: "processado_erro",
}

# Enum SituacaoConselhoClasse: 1 = em andamento, 2 = concluído. O bucket
# "não iniciados" não é contagem direta — é calculado (ver mapear_conselho).
_CONSELHO_EM_ANDAMENTO = 1
_CONSELHO_CONCLUIDO = 2


def mapear_usuarios(
    acesso_ativo: dict[str, int],
    de_unidades: dict[str, int],
) -> dict[str, Any]:
    """Monta o bloco ``usuarios`` do contrato."""
    return {
        "com_acesso_ativo": {
            "valor": acesso_ativo["valor"],
            "variacao_30_dias": acesso_ativo["variacao_30_dias"],
        },
        "de_unidades_educacionais": {
            "total": de_unidades["total"],
            "diretorias_regionais": de_unidades["diretorias_regionais"],
        },
        "unicos_por_dia": None,
        "acessos_por_hora": None,
    }


def mapear_fechamento(por_situacao: dict[int, int]) -> dict[str, int]:
    """Monta o bloco ``fechamento`` a partir das quantidades por status."""
    return {
        nome: int(por_situacao.get(codigo, 0))
        for codigo, nome in _FECHAMENTO_BUCKETS.items()
    }


def mapear_conselho_classe(
    por_situacao: dict[int, int],
    alunos_ativos: int,
) -> dict[str, int]:
    """Monta o bloco ``conselho_classe``.

    "Em andamento" e "processado com sucesso" (concluído) saem direto da
    query. "Não iniciados" é calculado: alunos ativos na turma menos os
    outros dois buckets (nunca negativo).
    """
    em_andamento = int(por_situacao.get(_CONSELHO_EM_ANDAMENTO, 0))
    concluido = int(por_situacao.get(_CONSELHO_CONCLUIDO, 0))
    nao_iniciados = max(alunos_ativos - (em_andamento + concluido), 0)
    return {
        "nao_iniciados": nao_iniciados,
        "em_andamento": em_andamento,
        "processado_sucesso": concluido,
    }


def mapear_frequencias() -> dict[str, Any]:
    """Monta o bloco ``frequencias``.

    Deferido: a query depende da janela de datas do bimestre, ainda não
    definida no discovery, e os valores precisam de ambiente com dado de
    2026 para validação. Retorna o bloco com indicadores nulos.
    """
    return {"lancadas": None, "esperadas": None, "percentual": None}


def mapear_sondagens() -> dict[str, Any]:
    """Monta o bloco ``sondagens``.

    ``realizadas`` é deferido (fonte no banco ``db_sondagem_qa``, ainda não
    conectado). ``esperadas`` é nulo por decisão do discovery: a fonte real
    é calculada ao vivo pelo serviço de Sondagem, sem réplica confiável.
    """
    return {"realizadas": None, "esperadas": None}
