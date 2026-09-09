"""Handlers dos dados do SERAp Estudantes."""

from typing import Any

from apps.serap import client
from apps.serap import mapper
from apps.serap import parser
from apps.serap import queries


def obter_provas(
    janela: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """Coleta e monta o bloco ``provas`` do contrato.

    Quando ``janela`` (inicio, fim) é informada, recorta por ``criado_em``;
    caso contrário devolve os números globais.
    """
    if janela is None:
        linhas = client.consultar(queries.PROVAS_AGREGADO)
    else:
        linhas = client.consultar(queries.PROVAS_AGREGADO_JANELA, janela)
    return mapper.mapear_provas(parser.parse_provas(linhas))
