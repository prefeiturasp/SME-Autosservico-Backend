"""Parser dos dados de usuários vindos do banco do SIGPAE."""

from typing import Any


def parse_acesso_ativo(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única da query de acesso ativo."""
    linha = linhas[0] if linhas else {}
    return {
        "total": int(linha.get("total") or 0),
        "ativos_30_dias": int(linha.get("ativos_30_dias") or 0),
        "novos_30_dias": int(linha.get("novos_30_dias") or 0),
    }


def parse_acessos(linhas: list[dict[str, Any]]) -> dict[str, int]:
    """Interpreta a linha única de acessos (únicos por dia e hoje)."""
    linha = linhas[0] if linhas else {}
    return {
        "unicos_por_dia": int(linha.get("unicos_por_dia") or 0),
        "acessos_hoje": int(linha.get("acessos_hoje") or 0),
    }


_COMPARATIVO_PERIODOS = ("dia", "quinzena", "mes", "trimestre")


def parse_comparativo_acessos(
    linhas: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Interpreta os 12 baldes (3 por período) numa linha única."""
    linha = linhas[0] if linhas else {}
    return {
        periodo: [
            int(linha.get(f"{periodo}_{ordem}") or 0) for ordem in (1, 2, 3)
        ]
        for periodo in _COMPARATIVO_PERIODOS
    }


def parse_por_tipo_perfil(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta as linhas de usuários por tipo de perfil."""
    return {
        str(linha["visao"]).upper(): int(linha["total_usuarios"] or 0)
        for linha in linhas
        if linha.get("visao")
    }


def parse_medicoes_por_status(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta as linhas de solicitações de medição agrupadas por status."""
    return {
        str(linha["status"]): int(linha["total"] or 0)
        for linha in linhas
        if linha.get("status")
    }


_PRODUTOS_CAMPOS = (
    "total_cadastrados",
    "homologados",
    "solicitacoes_no_mes",
    "solicitacoes_no_ano",
)


def parse_produtos_homologados(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta a linha única do agregado de produtos homologados."""
    linha = linhas[0] if linhas else {}
    return {campo: int(linha.get(campo) or 0) for campo in _PRODUTOS_CAMPOS}


def parse_empresas_terceirizadas(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta a linha única do agregado de empresas terceirizadas."""
    linha = linhas[0] if linhas else {}
    return {
        "cadastradas": int(linha.get("cadastradas") or 0),
        "ativas": int(linha.get("ativas") or 0),
    }


_SOLICITACAO_CAMPOS = (
    "total",
    "autorizadas",
    "aguardando",
    "negadas",
    "canceladas",
)
_SOLICITACAO_PERIODOS = ("dia", "quinzena", "mes", "trimestre")


def parse_solicitacoes_por_periodo(
    linhas: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Interpreta as linhas de solicitações (uma por período).

    Garante os 4 períodos, preenchendo com zeros os que não voltarem.
    """
    por_periodo = {
        str(linha["periodo"]): {
            campo: int(linha.get(campo) or 0) for campo in _SOLICITACAO_CAMPOS
        }
        for linha in linhas
        if linha.get("periodo")
    }
    return {
        periodo: por_periodo.get(
            periodo, dict.fromkeys(_SOLICITACAO_CAMPOS, 0)
        )
        for periodo in _SOLICITACAO_PERIODOS
    }


def _parse_linha_unica(
    linhas: list[dict[str, Any]], campos: tuple[str, ...]
) -> dict[str, int]:
    """Interpreta a linha única de um agregado, zerando o que faltar."""
    linha = linhas[0] if linhas else {}
    return {campo: int(linha.get(campo) or 0) for campo in campos}


_CRONOGRAMAS_CAMPOS = ("aguardando", "enviadas", "aprovadas")
_FICHAS_CAMPOS = (
    "cadastradas",
    "aprovadas",
    "em_analise",
    "pendentes_correcao",
)
_LAYOUTS_CAMPOS = (
    "cadastrados",
    "aprovados",
    "aguardando_codae",
    "pendentes_correcao",
)
_FORNECEDORES_CAMPOS = ("cadastradas", "ativas")


def parse_cronogramas_entregas(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta o agregado de cronogramas de entregas."""
    return _parse_linha_unica(linhas, _CRONOGRAMAS_CAMPOS)


def parse_fichas_tecnicas_produtos(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta o agregado de fichas técnicas de produtos."""
    return _parse_linha_unica(linhas, _FICHAS_CAMPOS)


def parse_layouts_embalagens(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta o agregado de layouts de embalagens."""
    return _parse_linha_unica(linhas, _LAYOUTS_CAMPOS)


def parse_fornecedores_distribuidores(
    linhas: list[dict[str, Any]],
) -> dict[str, int]:
    """Interpreta o agregado de fornecedores e distribuidores."""
    return _parse_linha_unica(linhas, _FORNECEDORES_CAMPOS)
