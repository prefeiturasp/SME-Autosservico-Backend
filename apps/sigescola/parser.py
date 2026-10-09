"""Parser dos dados vindos do banco do SIG-Escola."""

from typing import Any


def parse_por_situacao(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta linhas ``(situacao, quantidade)`` num dicionário."""
    return {
        str(linha["situacao"]): int(linha["quantidade"] or 0)
        for linha in linhas
        if linha.get("situacao") is not None
    }


def parse_inteiro(linhas: list[dict[str, Any]], campo: str) -> int:
    """Extrai um inteiro da primeira linha do resultado."""
    linha = linhas[0] if linhas else {}
    return int(linha.get(campo) or 0)


def parse_valor(linhas: list[dict[str, Any]], campo: str) -> float:
    """Extrai um valor monetário (``Decimal``) da primeira linha."""
    linha = linhas[0] if linhas else {}
    return float(linha.get(campo) or 0)


def parse_logins(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de logins (hoje e 30 dias anteriores)."""
    linha = linhas[0] if linhas else {}
    return {
        campo: int(linha.get(campo) or 0)
        for campo in (
            "unicos_hoje",
            "acessos_hoje",
            "usuarios_dia_30_dias",
            "acessos_30_dias",
        )
    }


def parse_periodos(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpreta os períodos do PTRF (o mais recente primeiro)."""
    return [
        {
            "referencia": str(linha["referencia"]),
            "data_inicio": linha["data_inicio"],
            "data_fim": linha["data_fim"],
        }
        for linha in linhas
    ]


def parse_unidades(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpreta as unidades (código EOL, tipo e nome) de uma DRE."""
    return [
        {
            "codigo_eol": str(linha["codigo_eol"]),
            "tipo_unidade": linha.get("tipo_unidade"),
            "nome": str(linha["nome"]),
        }
        for linha in linhas
    ]
