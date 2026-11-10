"""Mapper dos dados do Bens Físicos para o contrato de entrega ao BFF."""

from typing import Any

_CASAS_VARIACAO = 1


def sigla_curta(sigla: str | None, nome: str) -> str:
    """Último trecho da sigla (``PMSP/SME/SMECOTIC`` -> ``SMECOTIC``).

    Sem sigla aproveitável, usa o nome da unidade.
    """
    trechos = [t.strip() for t in (sigla or "").split("/") if t.strip()]
    return trechos[-1] if trechos else nome


def variacao_percentual(hoje: int, media: float) -> float | None:
    """Variação de hoje sobre a média diária; sem média, não há variação."""
    if not media:
        return None
    return round((hoje - media) / media * 100, _CASAS_VARIACAO)


def mapear_usuarios(
    ativos: int, unicos_hoje: int, media_diaria: float
) -> dict[str, Any]:
    """Monta o bloco ``usuarios``."""
    return {
        "com_acesso_ativo": {"valor": ativos},
        "unicos_por_dia": {
            "valor": unicos_hoje,
            "variacao_percentual_30_dias": variacao_percentual(
                unicos_hoje, media_diaria
            ),
        },
    }


def mapear_cadastro(
    totais: dict[str, int], por_unidade: list[dict[str, Any]]
) -> dict[str, Any]:
    """Monta o bloco ``cadastro_de_bens``, com as unidades em ordem desc."""
    unidades = [
        {
            "sigla": sigla_curta(unidade["sigla"], unidade["nome"]),
            "nome": unidade["nome"],
            "bens": unidade["bens"],
        }
        for unidade in por_unidade
    ]
    return {
        "bens_cadastrados": totais["bens_cadastrados"],
        "aguardando_aprovacao": totais["aguardando_aprovacao"],
        "por_unidade_administrativa": sorted(
            unidades, key=lambda u: (-u["bens"], u["sigla"])
        ),
    }


def mapear_baixas(totais: dict[str, int]) -> dict[str, int]:
    """Monta o bloco ``baixas_fisicas`` (contagem por pedido)."""
    return {
        "aprovadas": totais["aprovadas"],
        "aguardando_aprovacao": totais["aguardando_aprovacao"],
    }


def mapear_movimentacoes(
    totais: dict[str, int], transferencias: int
) -> dict[str, int]:
    """Monta o bloco ``movimentacoes`` (contagem por pedido)."""
    return {
        "realizadas": totais["realizadas"],
        "pendentes": totais["pendentes"],
        "transferencias_realizadas": transferencias,
    }
