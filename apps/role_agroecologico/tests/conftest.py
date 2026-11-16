"""Fixtures dos testes do Rolê Agroecológico."""

from collections.abc import Iterator
from datetime import datetime
from typing import Any
from unittest.mock import patch

import phpserialize
import pytest

from apps.role_agroecologico import queries

AGORA = datetime(2026, 11, 10, 10, 0)


def php(valor: Any) -> str:
    """Serializa no formato do PHP, como o WordPress grava no banco."""
    serializado: bytes = phpserialize.dumps(valor)
    return serializado.decode()


def turmas(*alunos_por_turma: list[dict[str, Any]]) -> str:
    """``dados_turmas`` serializado, uma turma por lista de alunos."""
    return php(
        [
            {"idTurma": str(n), "nomeTurma": f"Turma {n}", "alunosTurma": a}
            for n, a in enumerate(alunos_por_turma, start=1)
        ]
    )


def inscricao(**campos: Any) -> dict[str, Any]:
    """Linha da query de inscrições, com valores padrão neutros."""
    return {
        "id": 1,
        "criada_em": datetime(2026, 1, 1),
        "status": "pendente",
        "dre": "DRE Butantã",
        "codigo_eol_ue": "000001",
        "data_reservada": None,
        "dados_turmas": None,
        "dados_educadores": None,
        "dados_acompanhantes": None,
        "oferta_almoco": None,
        "ids_up_roteiro": None,
        **campos,
    }


PRESENTE = {"nome": "Ana", "confirmacaoPresenca": True}
AUSENTE = {"nome": "Bia", "confirmacaoPresenca": False}

INSCRICOES = [
    # Realizada com almoço: 2 alunos presentes e 1 ausente, 1 educador e
    # 1 acompanhante presentes.
    inscricao(
        id=10,
        status="realizado",
        dre="DRE Butantã",
        codigo_eol_ue="000001",
        dados_turmas=turmas([PRESENTE, AUSENTE], [PRESENTE]),
        dados_educadores=php([PRESENTE]),
        dados_acompanhantes=php([PRESENTE]),
        oferta_almoco="1",
        ids_up_roteiro=php(["692", "691"]),
    ),
    # Realizada sem almoço, mesma UE: 1 aluno presente, educador ausente.
    inscricao(
        id=11,
        status="realizado",
        dre="DRE Butantã",
        codigo_eol_ue="000001",
        dados_turmas=turmas([PRESENTE]),
        dados_educadores=php([AUSENTE]),
        oferta_almoco="0",
        ids_up_roteiro=php(["692", "999"]),
    ),
    # Agendada para daqui a 3 dias, criada ontem, sem DRE.
    inscricao(
        id=12,
        criada_em=datetime(2026, 11, 9, 15, 0),
        status="aprovado",
        dre="",
        codigo_eol_ue="000002",
        data_reservada="20261113",
        dados_turmas=turmas([PRESENTE, PRESENTE]),
        ids_up_roteiro=php(["690"]),
    ),
    # Cancelada: não conta como inscrita nem como prevista.
    inscricao(
        id=13,
        status="cancelado",
        dre="DRE Penha",
        codigo_eol_ue="000003",
        data_reservada="2026-11-12",
        dados_turmas=turmas([PRESENTE]),
    ),
]

UNIDADES_PRODUTIVAS = [
    {"id": 690, "nome": "Sítio Raízes", "preservacao": 0},
    {"id": 691, "nome": "horta Jardim", "preservacao": 1},
    {"id": 692, "nome": "Fazenda Vale", "preservacao": 1},
]


class Banco:
    """Banco do Rolê simulado, respondendo por query."""

    def __init__(self) -> None:
        """Começa com as linhas de exemplo e sem consultas."""
        self.respostas: dict[str, list[dict[str, Any]]] = {
            queries.INSCRICOES: INSCRICOES,
            queries.UNIDADES_PRODUTIVAS: UNIDADES_PRODUTIVAS,
        }
        self.consultas: list[str] = []

    def consultar(self, query: str, params: Any = ()) -> list[dict[str, Any]]:
        """Devolve as linhas cadastradas para a query."""
        self.consultas.append(query)
        return self.respostas[query]


@pytest.fixture
def banco() -> Iterator[Banco]:
    """Troca o cliente do Rolê pelo banco simulado."""
    simulado = Banco()
    with patch("apps.role_agroecologico.client.consultar", simulado.consultar):
        yield simulado
