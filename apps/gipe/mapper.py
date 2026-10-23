"""Mapper dos dados do GIPE para o contrato de entrega ao BFF."""

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

NAO_INFORMADO = "Não informado"

# "DIRETORIA REGIONAL DE EDUCACAO IPIRANGA" -> "Ipiranga".
_PREFIXO_DRE = re.compile(
    r"^DIRETORIA\s+REGIONAL\s+DE\s+EDUCA[CÇ][AÃ]O\s+", re.IGNORECASE
)
_PARTICULAS = frozenset({"de", "do", "da", "dos", "das", "e"})

# Cargo (``users_cargo.nome``) -> rótulo do painel.
_ROTULOS_CARGO = {
    "DIRETOR DE ESCOLA": "Diretor de Escola",
    "ASSISTENTE DE DIRETOR DE ESCOLA": "Assistente de direção",
    "PONTO FOCAL DRE": "Ponto focal",
    "GIPE": "GIPE",
}

_MESES = (
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)

_CASAS_DIAS = 3


def _titulo(texto: str) -> str:
    """Title case, com partículas (de, do, da...) em minúsculas."""
    palavras = texto.lower().split()
    return " ".join(
        palavra if indice and palavra in _PARTICULAS else palavra.title()
        for indice, palavra in enumerate(palavras)
    )


def nome_curto_dre(nome: str) -> str:
    """Nome curto da DRE, como o painel exibe."""
    return _titulo(_PREFIXO_DRE.sub("", nome.strip()))


def rotulo_perfil(cargo: str, admin: bool) -> str:
    """Rótulo do perfil a partir do cargo e da flag de administrador."""
    rotulo = _ROTULOS_CARGO.get(cargo.strip().upper(), _titulo(cargo))
    return f"{rotulo} admin" if admin else rotulo


def _itens(contagens: dict[str, int]) -> list[dict[str, Any]]:
    """``rótulo -> total`` em itens ``{label, value}``, desc."""
    return [
        {"label": label, "value": value}
        for label, value in sorted(
            contagens.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def _por_unidade(
    contagem: dict[str, int], nomes: dict[str, str], *, dre: bool
) -> list[dict[str, Any]]:
    """Troca os códigos EOL pelos nomes (o próprio código se não achar)."""
    rotulos: dict[str, int] = {}
    for codigo, total in contagem.items():
        if not codigo:
            rotulo = NAO_INFORMADO
        elif codigo in nomes:
            nome = nomes[codigo]
            rotulo = nome_curto_dre(nome) if dre else nome
        else:
            rotulo = codigo
        rotulos[rotulo] = rotulos.get(rotulo, 0) + total
    return _itens(rotulos)


def _plural(quantidade: int, singular: str, plural: str) -> str:
    """Escolhe a forma pela quantidade."""
    return singular if quantidade == 1 else plural


def _kpi(
    valor: int, tendencia: str | None = None, label: str | None = None
) -> dict[str, Any]:
    """KPI no formato do contrato."""
    return {"valor": valor, "tendencia": tendencia, "tendencia_label": label}


def mapear_kpis(dados: dict[str, int]) -> dict[str, Any]:
    """Monta o bloco ``kpis``.

    Sem histórico de login, "acessos hoje" repete "usuários únicos" e os
    dois ficam sem tendência.
    """
    novos = dados["novos_30_dias"]
    acesso_ativo = (
        _kpi(
            dados["com_acesso_ativo"],
            "above",
            f"{novos} {_plural(novos, 'novo', 'novos')} nos últimos 30 dias",
        )
        if novos
        else _kpi(dados["com_acesso_ativo"])
    )
    return {
        "acesso_ativo": acesso_ativo,
        "usuarios_unicos": _kpi(dados["unicos_hoje"]),
        "acessos_hoje": _kpi(dados["unicos_hoje"]),
    }


def _arredondar_dias(dias: float | None) -> float | None:
    """Arredonda uma média de dias, preservando ``None``."""
    return None if dias is None else round(dias, _CASAS_DIAS)


def tendencia_tempo(
    atual: float | None, anterior: float | None
) -> tuple[str | None, str | None]:
    """Compara os últimos 30 dias com os 30 anteriores.

    Tempo menor é melhor: ``below`` = mais rápido, ``above`` = mais
    lento. Sem dado numa das janelas, ou sem variação, não há tendência.
    """
    if atual is None or not anterior:
        return None, None
    variacao = round((atual - anterior) / anterior * 100)
    if variacao < 0:
        return "below", f"{-variacao}% mais rápido"
    if variacao > 0:
        return "above", f"{variacao}% mais lento"
    return None, None


def mapear_tempo_resposta(dias: dict[str, float | None]) -> dict[str, Any]:
    """Monta o card de tempo de resposta (média em dias + tendência)."""
    resolucao, resolucao_label = tendencia_tempo(
        dias["resolucao_30d"], dias["resolucao_30d_anterior"]
    )
    tratativa, tratativa_label = tendencia_tempo(
        dias["tratativa_30d"], dias["tratativa_30d_anterior"]
    )
    return {
        "tempo_medio_resolucao_dias": _arredondar_dias(dias["resolucao"]),
        "tendencia_resolucao": resolucao,
        "tendencia_resolucao_label": resolucao_label,
        "tempo_medio_primeira_tratativa_dias": _arredondar_dias(
            dias["tratativa"]
        ),
        "tendencia_primeira_tratativa": tratativa,
        "tendencia_primeira_tratativa_label": tratativa_label,
    }


def mapear_por_mes(serie: list[tuple[date, int]]) -> list[dict[str, Any]]:
    """Série mensal com rótulo ``Abril/26`` e o primeiro mês de pico."""
    pico = max((total for _, total in serie), default=None)
    itens = []
    marcado = False
    for mes, total in serie:
        e_pico = not marcado and total == pico
        marcado = marcado or e_pico
        itens.append(
            {
                "label": f"{_MESES[mes.month - 1]}/{mes.year % 100:02d}",
                "valor": total,
                "pico": e_pico,
            }
        )
    return itens


def mapear_por_bimestre(por_bimestre: dict[int, int]) -> list[dict[str, Any]]:
    """Ocorrências por bimestre (corte fixo por mês), em ordem."""
    return [
        {"label": f"{bimestre}º Bimestre", "value": total}
        for bimestre, total in sorted(por_bimestre.items())
    ]


def _formatar_dias(dias: float) -> str:
    """Tempo médio por extenso, com vírgula: ``"2,5 dias"``."""
    return f"{dias:.1f}".replace(".", ",") + " dias"


def mapear_analistas(
    analistas: list[dict[str, Any]], nomes: dict[str, str]
) -> list[dict[str, Any]]:
    """Ocorrências tratadas por analista; sem nome resolvido, fica o RF."""
    itens = [
        {
            "analista": nomes.get(analista["username"], analista["username"]),
            "ocorrencias_tratadas": analista["ocorrencias_tratadas"],
            "tempo_medio": _formatar_dias(analista["tempo_medio_dias"]),
        }
        for analista in analistas
    ]
    return sorted(
        itens,
        key=lambda item: (-item["ocorrencias_tratadas"], item["analista"]),
    )


@dataclass(frozen=True)
class DadosOcorrencias:
    """Cards de ocorrências já interpretados pelo parser."""

    status_geral: dict[str, int]
    tempos: dict[str, float | None]
    sem_movimentacao_7_dias: int
    media_movimentacoes: float | None
    por_dre: dict[str, int]
    por_ue: dict[str, int]
    por_categoria: dict[str, int]
    por_tipo: dict[bool, dict[str, int]]
    por_mes: list[tuple[date, int]]
    por_bimestre: dict[int, int]
    analistas: list[dict[str, Any]]
    tratadas_por_dre: dict[str, int]


@dataclass(frozen=True)
class Nomes:
    """Nomes buscados no banco de usuários: unidades (EOL) e analistas (RF)."""

    unidades: dict[str, str]
    analistas: dict[str, str]


def mapear_ocorrencias(
    dados: DadosOcorrencias, nomes: Nomes
) -> dict[str, Any]:
    """Monta o bloco ``ocorrencias``.

    "Dentro/fora do prazo" ficam nulos: o GIPE não tem SLA definido.
    """
    media = dados.media_movimentacoes
    return {
        "status_geral": {
            "cadastrados": dados.status_geral["cadastrados"],
            "abertas": dados.status_geral["abertas"],
            "em_andamento": dados.status_geral["em_andamento"],
            "finalizadas": dados.status_geral["finalizadas"],
        },
        "tempo_resposta": mapear_tempo_resposta(dados.tempos),
        "prazos_movimentacoes": {
            "dentro_do_prazo": None,
            "fora_do_prazo": None,
            "sem_movimentacao_7_dias": dados.sem_movimentacao_7_dias,
            "media_movimentacoes_por_ocorrencia": (
                None if media is None else round(media, 1)
            ),
        },
        "por_dre": _por_unidade(dados.por_dre, nomes.unidades, dre=True),
        "por_unidade_educacional": _por_unidade(
            dados.por_ue, nomes.unidades, dre=False
        ),
        "por_categoria": {
            "patrimoniais": dados.por_categoria["patrimoniais"],
            "interpessoais": dados.por_categoria["interpessoais"],
        },
        "por_tipo_patrimonial": _itens(dados.por_tipo[True]),
        "por_tipo_interpessoal": _itens(dados.por_tipo[False]),
        "por_mes": mapear_por_mes(dados.por_mes),
        "por_periodo_letivo": mapear_por_bimestre(dados.por_bimestre),
        "tratadas_por_analista": mapear_analistas(
            dados.analistas, nomes.analistas
        ),
        "tratadas_por_dre": _por_unidade(
            dados.tratadas_por_dre, nomes.unidades, dre=True
        ),
    }


def _com_nome(
    linhas: list[dict[str, Any]], *, dre: bool
) -> list[dict[str, Any]]:
    """Contagem por unidade que já veio com o nome do banco de usuários."""
    contagem = {linha["codigo"]: linha["total"] for linha in linhas}
    nomes = {
        linha["codigo"]: linha["nome"] for linha in linhas if linha["nome"]
    }
    return _por_unidade(contagem, nomes, dre=dre)


def mapear_usuarios(
    *,
    cadastrados: int,
    perfis: list[dict[str, Any]],
    por_dre: list[dict[str, Any]],
    por_ue: list[dict[str, Any]],
) -> dict[str, Any]:
    """Monta o bloco ``usuarios``.

    "Por tipo de perfil" (percentual) e "perfis mais utilizados" saem da
    mesma contagem de usuários por perfil: não há log de acesso no GIPE.
    """
    por_perfil: dict[str, int] = {}
    for perfil in perfis:
        rotulo = rotulo_perfil(perfil["cargo"], perfil["admin"])
        por_perfil[rotulo] = por_perfil.get(rotulo, 0) + perfil["total"]
    itens = _itens(por_perfil)
    soma = sum(por_perfil.values())
    return {
        "cadastrados": cadastrados,
        "por_tipo_de_perfil": [
            {
                "label": item["label"],
                "percentage": round(item["value"] / soma * 100) if soma else 0,
            }
            for item in itens
        ],
        "perfis_mais_utilizados": itens,
        "por_dre": _com_nome(por_dre, dre=True),
        "por_unidade_educacional": _com_nome(por_ue, dre=False),
    }


def mapear_produtividade(
    movimentacoes: dict[str, int], anexos_enviados: int
) -> dict[str, int]:
    """Monta o bloco ``produtividade``.

    Atualizações = criação de cada ocorrência + estágios concluídos.
    """
    return {
        "encaminhamentos_realizados": movimentacoes["encaminhamentos"],
        "anexos_enviados": anexos_enviados,
        "atualizacoes_nas_ocorrencias": (
            movimentacoes["ocorrencias"] + movimentacoes["encaminhamentos"]
        ),
    }
