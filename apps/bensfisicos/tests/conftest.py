"""Banco simulado do Bens Físicos: cada query devolve as linhas cadastradas."""

from collections.abc import Iterator
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest

from apps.bensfisicos import queries

# Números do banco de homologação usados no discovery (AB#158715).
RESPOSTAS: dict[str, list[dict[str, Any]]] = {
    queries.USUARIOS_ATIVOS: [{"com_acesso_ativo": 6}],
    queries.USUARIOS_UNICOS: [
        {"unicos_hoje": 1, "media_diaria_30_dias": Decimal("0.3")}
    ],
    queries.BENS: [{"bens_cadastrados": 6083, "aguardando_aprovacao": 53}],
    queries.BENS_POR_UNIDADE: [
        {
            "sigla": "PMSP/SME/SME-GAB/SMECOTIC",
            "nome": "COORDENADORIA DE TECNOLOGIA",
            "bens": 493,
        },
        {"sigla": "SPDM", "nome": "SPDM", "bens": 339},
    ],
    queries.BAIXAS_FISICAS: [{"aprovadas": 42, "aguardando_aprovacao": 0}],
    queries.MOVIMENTACOES: [{"realizadas": 1461, "pendentes": 80}],
    queries.TRANSFERENCIAS: [{"transferencias_realizadas": 7}],
}


@pytest.fixture
def banco() -> Iterator[list[str]]:
    """Simula o banco do Bens Físicos; devolve as queries recebidas."""
    chamadas: list[str] = []

    def consultar(query: str, params: Any = ()) -> list[dict[str, Any]]:
        chamadas.append(query)
        return RESPOSTAS[query]

    with patch("apps.bensfisicos.client.consultar", side_effect=consultar):
        yield chamadas
