"""Parser dos dados vindos do banco do Rolê Agroecológico.

Os campos serializados do PHP são desserializados aqui, uma vez por linha,
e viram tipos simples para o mapper contar.
"""

import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from typing import Any

import phpserialize

logger = logging.getLogger(__name__)

# Valores de ``confirmacaoPresenca`` que marcam ausência. O site grava
# booleano ou o texto vindo do formulário (``False`` também casa com 0).
_AUSENTE = frozenset({False, "", "0", "false"})

_FORMATOS_DATA = ("%Y%m%d", "%Y-%m-%d")


@dataclass(frozen=True)
class Inscricao:
    """Agendamento de uma UE num roteiro, já interpretado."""

    id: int
    criada_em: datetime
    status: str
    dre: str | None
    codigo_eol_ue: str | None
    data_reservada: date | None
    oferta_almoco: bool
    alunos: list[dict[str, Any]] = field(default_factory=list)
    educadores: list[dict[str, Any]] = field(default_factory=list)
    acompanhantes: list[dict[str, Any]] = field(default_factory=list)
    ids_ups: frozenset[int] = frozenset()


@dataclass(frozen=True)
class UnidadeProdutiva:
    """UP publicada no site."""

    id: int
    nome: str
    preservacao: bool


def _como_lista(valor: Any) -> Any:
    """Troca os arrays do PHP (dict de índices inteiros) por listas."""
    if isinstance(valor, dict):
        itens = {chave: _como_lista(item) for chave, item in valor.items()}
        if all(isinstance(chave, int) for chave in itens):
            return [itens[chave] for chave in sorted(itens)]
        return itens
    return valor


def desserializar(valor: str | None, *, post_id: int, campo: str) -> Any:
    """Desserializa um campo do PHP; vazio ou inválido vira ``[]``.

    O tamanho das strings no formato do PHP é em bytes, por isso o texto
    volta para UTF-8 antes de desserializar.
    """
    if not valor:
        return []
    try:
        return _como_lista(
            phpserialize.loads(valor.encode(), decode_strings=True)
        )
    except ValueError:
        logger.warning(
            "Campo %s do post %s não é um array serializado válido",
            campo,
            post_id,
        )
        return []


def _lista_de_dicts(valor: Any) -> list[dict[str, Any]]:
    """Mantém só os itens que são dicionários."""
    if not isinstance(valor, list):
        return []
    return [item for item in valor if isinstance(item, dict)]


def _alunos(turmas: Any) -> list[dict[str, Any]]:
    """Alunos de todas as turmas (``dados_turmas[*].alunosTurma``)."""
    return [
        aluno
        for turma in _lista_de_dicts(turmas)
        for aluno in _lista_de_dicts(turma.get("alunosTurma"))
    ]


def _ids(valor: Any) -> frozenset[int]:
    """IDs de post de uma lista serializada, ignorando o que não é número."""
    if not isinstance(valor, list):
        return frozenset()
    return frozenset(int(item) for item in valor if str(item).isdigit())


def _data(valor: str | None) -> date | None:
    """Data reservada em ``Ymd`` ou ``Y-m-d``; o resto vira ``None``."""
    for formato in _FORMATOS_DATA:
        try:
            return datetime.strptime(valor or "", formato).date()
        except ValueError:
            continue
    return None


def _texto(valor: str | None) -> str | None:
    """Texto sem espaços nas pontas; vazio vira ``None``."""
    return (valor or "").strip() or None


def presente(pessoa: dict[str, Any]) -> bool:
    """Presença como o site considera: sem marcação, está presente."""
    marcacao = pessoa.get("confirmacaoPresenca", True)
    if isinstance(marcacao, str):
        marcacao = marcacao.strip().lower()
    elif not isinstance(marcacao, int | float | None):
        return bool(marcacao)
    return marcacao not in _AUSENTE


def _inscricao(linha: dict[str, Any]) -> Inscricao:
    """Interpreta uma linha de inscrição."""
    post_id = int(linha["id"])

    def _serializado(campo: str) -> Any:
        return desserializar(linha[campo], post_id=post_id, campo=campo)

    return Inscricao(
        id=post_id,
        criada_em=linha["criada_em"],
        status=_texto(linha["status"]) or "",
        dre=_texto(linha["dre"]),
        codigo_eol_ue=_texto(linha["codigo_eol_ue"]),
        data_reservada=_data(linha["data_reservada"]),
        oferta_almoco=linha["oferta_almoco"] == "1",
        alunos=_alunos(_serializado("dados_turmas")),
        educadores=_lista_de_dicts(_serializado("dados_educadores")),
        acompanhantes=_lista_de_dicts(_serializado("dados_acompanhantes")),
        ids_ups=_ids(_serializado("ids_up_roteiro")),
    )


def parse_inscricoes(linhas: list[dict[str, Any]]) -> list[Inscricao]:
    """Interpreta as linhas de inscrição, uma por agendamento."""
    return [_inscricao(linha) for linha in linhas]


def parse_unidades_produtivas(
    linhas: list[dict[str, Any]],
) -> list[UnidadeProdutiva]:
    """Interpreta as linhas de UP publicada."""
    return [
        UnidadeProdutiva(
            id=int(linha["id"]),
            nome=(linha["nome"] or "").strip(),
            preservacao=bool(linha["preservacao"]),
        )
        for linha in linhas
    ]
