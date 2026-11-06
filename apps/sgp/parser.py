"""Parser dos dados vindos do banco do SGP."""

from typing import Any


def parse_acesso_ativo(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de usuários com acesso ativo."""
    linha = linhas[0] if linhas else {}
    return {
        "valor": int(linha.get("total") or 0),
        "variacao_30_dias": int(linha.get("ativos_30_dias") or 0),
    }


def parse_de_unidades(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de usuários de unidades educacionais."""
    linha = linhas[0] if linhas else {}
    return {
        "total": int(linha.get("total") or 0),
        "diretorias_regionais": int(linha.get("diretorias") or 0),
    }


def parse_por_dre_situacao(
    linhas: list[dict[str, Any]],
) -> dict[str, dict[int, int]]:
    """Interpreta linhas ``(dre, situacao, quantidade)`` por DRE."""
    por_dre: dict[str, dict[int, int]] = {}
    for linha in linhas:
        if linha.get("dre") is None or linha.get("situacao") is None:
            continue
        situacoes = por_dre.setdefault(str(linha["dre"]), {})
        situacao = int(linha["situacao"])
        situacoes[situacao] = situacoes.get(situacao, 0) + int(
            linha["quantidade"] or 0
        )
    return por_dre


def parse_previsto_por_dre(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta linhas ``(dre, previsto)`` num dicionário."""
    return {
        str(linha["dre"]): int(linha["previsto"] or 0)
        for linha in linhas
        if linha.get("dre") is not None
    }


def parse_periodos(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpreta as linhas de bimestres do calendário escolar."""
    return [
        {
            "ano_letivo": int(linha["ano_letivo"]),
            "modalidade": int(linha["modalidade"]),
            "semestre": (
                int(linha["semestre"])
                if linha.get("semestre") is not None
                else None
            ),
            "bimestre": int(linha["bimestre"]),
            "inicio": linha["inicio"],
            "fim": linha["fim"],
        }
        for linha in linhas
    ]


def parse_sondagens(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de sondagens (realizadas/esperadas)."""
    linha = linhas[0] if linhas else {}
    return {
        "realizadas": int(linha.get("realizadas") or 0),
        "esperadas": int(linha.get("esperadas") or 0),
    }


def parse_frequencias(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de frequências (lançadas/esperadas)."""
    linha = linhas[0] if linhas else {}
    return {
        "lancadas": int(linha.get("lancadas") or 0),
        "esperadas": int(linha.get("esperadas") or 0),
    }
