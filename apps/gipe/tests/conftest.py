"""Bancos simulados do GIPE: cada query devolve as linhas cadastradas."""

from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest

from apps.gipe import queries

# Números do banco local usado no discovery (2 ocorrências, 11 usuários).
OCORRENCIAS: dict[str, list[dict[str, Any]]] = {
    queries.STATUS_GERAL: [
        {"cadastrados": 2, "abertas": 0, "em_andamento": 1, "finalizadas": 1}
    ],
    queries.TEMPO_RESPOSTA: [
        {
            "resolucao": Decimal("0.0042"),
            "resolucao_30d": Decimal("2.0"),
            "resolucao_30d_anterior": Decimal("2.5"),
            "tratativa": Decimal("0.0012"),
            "tratativa_30d": None,
            "tratativa_30d_anterior": None,
        }
    ],
    queries.SEM_MOVIMENTACAO_7_DIAS: [{"total": 1}],
    queries.MOVIMENTACOES: [
        {
            "ocorrencias": 2,
            "encaminhamentos": 2,
            "media_por_ocorrencia": Decimal("2.0"),
        }
    ],
    queries.POR_DRE: [{"codigo": "108600", "total": 2}],
    queries.POR_UE: [{"codigo": "019455", "total": 2}],
    queries.POR_CATEGORIA: [{"patrimoniais": 1, "interpessoais": 1}],
    queries.POR_TIPO: [
        {"patrimonial": True, "nome": "Furto", "total": 1},
        {"patrimonial": False, "nome": "Bullying", "total": 1},
    ],
    queries.POR_MES: [{"mes": date(2026, 4, 1), "total": 2}],
    queries.POR_BIMESTRE: [{"bimestre": 1, "total": 2}],
    queries.TRATADAS_POR_ANALISTA: [
        {
            "username": "7210418",
            "ocorrencias_tratadas": 1,
            "tempo_medio_dias": Decimal("0.0042"),
        }
    ],
    queries.TRATADAS_POR_DRE: [{"codigo": "108600", "total": 1}],
}

ANEXOS: dict[str, list[dict[str, Any]]] = {
    queries.ANEXOS_ENVIADOS: [{"total": 0}],
}

USUARIOS: dict[str, list[dict[str, Any]]] = {
    queries.KPIS_USUARIOS: [
        {
            "cadastrados": 11,
            "com_acesso_ativo": 7,
            "novos_30_dias": 1,
            "unicos_hoje": 3,
        }
    ],
    queries.UNIDADES_POR_CODIGO: [
        {
            "codigo": "108600",
            "nome": "DIRETORIA REGIONAL DE EDUCACAO IPIRANGA",
        },
        {"codigo": "019455", "nome": "EMEF PERICLES EUGENIO DA SILVA RAMOS"},
    ],
    queries.NOMES_POR_USERNAME: [],
    queries.USUARIOS_POR_PERFIL: [
        {"cargo": "DIRETOR DE ESCOLA", "admin": False, "total": 5},
        {"cargo": "GIPE", "admin": True, "total": 2},
        {"cargo": "GIPE", "admin": False, "total": 2},
        {"cargo": "PONTO FOCAL DRE", "admin": False, "total": 2},
    ],
    queries.USUARIOS_POR_DRE: [
        {
            "codigo": "108600",
            "nome": "DIRETORIA REGIONAL DE EDUCACAO IPIRANGA",
            "total": 5,
        }
    ],
    queries.USUARIOS_POR_UE: [
        {
            "codigo": "019455",
            "nome": "EMEF PERICLES EUGENIO DA SILVA RAMOS",
            "total": 5,
        }
    ],
}


@dataclass
class Bancos:
    """Respostas por query de cada banco e as chamadas recebidas."""

    ocorrencias: dict[str, list[dict[str, Any]]]
    anexos: dict[str, list[dict[str, Any]]]
    usuarios: dict[str, list[dict[str, Any]]]
    chamadas: list[tuple[str, str, Any]] = field(default_factory=list)

    def consultas(self, banco: str, query: str) -> list[Any]:
        """Parâmetros de cada chamada de ``query`` no ``banco``."""
        return [p for b, q, p in self.chamadas if b == banco and q == query]


@pytest.fixture
def bancos() -> Iterator[Bancos]:
    """Simula os três bancos do GIPE a partir das respostas acima.

    Cada query só existe no banco a que pertence: consultar no banco errado
    quebra o teste com ``KeyError``.
    """
    simulados = Bancos(dict(OCORRENCIAS), dict(ANEXOS), dict(USUARIOS))

    def _responder(
        banco: str, respostas: dict[str, list[dict[str, Any]]]
    ) -> Any:
        def consultar(query: str, params: Any = ()) -> list[dict[str, Any]]:
            simulados.chamadas.append((banco, query, params))
            return respostas[query]

        return consultar

    with (
        patch(
            "apps.gipe.client.consultar_ocorrencias",
            side_effect=_responder("ocorrencias", simulados.ocorrencias),
        ),
        patch(
            "apps.gipe.client.consultar_anexos",
            side_effect=_responder("anexos", simulados.anexos),
        ),
        patch(
            "apps.gipe.client.consultar_usuarios",
            side_effect=_responder("usuarios", simulados.usuarios),
        ),
    ):
        yield simulados
