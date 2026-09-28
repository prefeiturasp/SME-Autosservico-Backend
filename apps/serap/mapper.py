"""Mapper dos dados do SERAp para o contrato de entrega ao BFF."""

from typing import Any


def mapear_provas(agregado: dict[str, int]) -> dict[str, Any]:
    """Monta o bloco ``provas`` do contrato.

    ``percentual_finalizadas`` é a razão finalizadas/total em pontos
    percentuais (uma casa decimal); zero quando não há provas.
    """
    total = agregado["total"]
    finalizadas = agregado["finalizadas"]
    percentual = round(finalizadas / total * 100, 1) if total else 0.0
    return {
        "total": total,
        "iniciadas_hoje": agregado["iniciadas_hoje"],
        "nao_finalizadas": agregado["nao_finalizadas"],
        "finalizadas": finalizadas,
        "percentual_finalizadas": percentual,
    }
