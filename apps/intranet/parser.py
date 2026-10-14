"""Parser dos dados vindos do banco do Intranet."""

from typing import Any


def _inteiros(
    linhas: list[dict[str, Any]], campos: tuple[str, ...]
) -> dict[str, int]:
    """Lê campos inteiros da linha única do resultado.

    O MySQL devolve ``SUM`` como ``Decimal`` e ``NULL`` quando não há
    linhas a somar; ambos viram ``int`` (``NULL`` = 0).
    """
    linha = linhas[0] if linhas else {}
    return {campo: int(linha.get(campo) or 0) for campo in campos}


def parse_kpis(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única dos KPIs de usuário."""
    return _inteiros(linhas, ("com_acesso_ativo", "unicos_hoje"))


def parse_status_sorteios(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única do status geral de Sorteios."""
    return _inteiros(
        linhas, ("cadastrados", "realizados", "ativos", "encerrados")
    )


def parse_status_ordem(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única do status geral de Ordem de Inscrição."""
    return _inteiros(linhas, ("cadastrados", "ativos", "encerrados"))


def parse_contagem_por_chave(
    linhas: list[dict[str, Any]], campo: str
) -> dict[str | None, int]:
    """Interpreta linhas ``(campo, total)`` num dicionário.

    A chave pode ser ``None`` (ex.: post sem ``tipo_evento``); o rótulo
    desses casos é decidido no mapper.
    """
    return {linha.get(campo): int(linha["total"] or 0) for linha in linhas}


def parse_oportunidades(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de Oportunidades e Recrutamento."""
    return _inteiros(
        linhas,
        (
            "oportunidades_cadastradas",
            "cvs_cadastrados",
            "inscricoes_realizadas",
            "contratacoes_efetivadas",
        ),
    )
