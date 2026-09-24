"""Consultas SQL de leitura no banco do SIGPAE."""

USUARIOS_ACESSO_ATIVO = """
select
    count(*) filter (where last_login is not null) as total,
    count(*) filter (where last_login >= now() - interval '30 days')
        as ativos_30_dias,
    count(*) filter (where date_joined >= now() - interval '30 days')
        as novos_30_dias
from perfil_usuario
where is_active
"""

ACESSOS_UNICOS_HOJE = """
select
    (
        select coalesce(round(avg(u)), 0)
        from (
            select count(distinct actor_id) as u
            from auditlog_logentry
            where actor_id is not null
                and timestamp >= now() - interval '30 days'
            group by date(timestamp)
        ) x
    ) as unicos_por_dia,
    (
        select count(*)
        from auditlog_logentry
        where timestamp::date = current_date
    ) as acessos_hoje
"""

# Comparativo de acessos: 3 baldes por período, num único scan de
# auditlog_logentry. dia/quinzena/mês são janelas móveis terminando hoje;
# trimestre são os 3 meses do trimestre corrente.
COMPARATIVO_ACESSOS = """
select
    count(*) filter (where timestamp::date = current_date - 2) as dia_1,
    count(*) filter (where timestamp::date = current_date - 1) as dia_2,
    count(*) filter (where timestamp::date = current_date) as dia_3,
    count(*) filter (
        where timestamp >= now() - interval '45 days'
            and timestamp < now() - interval '30 days'
    ) as quinzena_1,
    count(*) filter (
        where timestamp >= now() - interval '30 days'
            and timestamp < now() - interval '15 days'
    ) as quinzena_2,
    count(*) filter (where timestamp >= now() - interval '15 days')
        as quinzena_3,
    count(*) filter (
        where timestamp >= now() - interval '21 days'
            and timestamp < now() - interval '14 days'
    ) as mes_1,
    count(*) filter (
        where timestamp >= now() - interval '14 days'
            and timestamp < now() - interval '7 days'
    ) as mes_2,
    count(*) filter (where timestamp >= now() - interval '7 days') as mes_3,
    count(*) filter (
        where timestamp >= date_trunc('quarter', now())
            and timestamp < date_trunc('quarter', now()) + interval '1 month'
    ) as trimestre_1,
    count(*) filter (
        where timestamp >= date_trunc('quarter', now()) + interval '1 month'
            and timestamp < date_trunc('quarter', now()) + interval '2 months'
    ) as trimestre_2,
    count(*) filter (
        where timestamp >= date_trunc('quarter', now()) + interval '2 months'
            and timestamp < date_trunc('quarter', now()) + interval '3 months'
    ) as trimestre_3
from auditlog_logentry
"""

USUARIOS_POR_TIPO_PERFIL = """
select pp.visao, count(distinct pv.usuario_id) as total_usuarios
from perfil_vinculo pv
join perfil_perfil pp on pp.id = pv.perfil_id
where pv.ativo
group by pp.visao
"""

MEDICOES_INICIAIS_POR_STATUS = """
select status, count(*) as total
from medicao_inicial_solicitacaomedicaoinicial
group by status
"""

PRODUTOS_HOMOLOGADOS = """
select
    (select count(*) from produto_produto) as total_cadastrados,
    (
        select count(*) from produto_homologacaoproduto
        where status = 'CODAE_HOMOLOGADO'
    ) as homologados,
    (
        select count(*) from produto_homologacaoproduto
        where date_trunc('month', criado_em) = date_trunc('month', now())
    ) as solicitacoes_no_mes,
    (
        select count(*) from produto_homologacaoproduto
        where extract(year from criado_em) = extract(year from now())
    ) as solicitacoes_no_ano
"""

EMPRESAS_TERCEIRIZADAS = """
select
    (
        select count(*) from terceirizada_terceirizada
        where tipo_empresa = 'TERCEIRIZADA'
    ) as cadastradas,
    (
        select count(distinct t.id)
        from terceirizada_terceirizada t
        join terceirizada_contrato ct on ct.terceirizada_id = t.id
        where t.tipo_empresa = 'TERCEIRIZADA' and not ct.encerrado
    ) as ativas
"""

# Janelas de data de cada período do seletor (Dia/Quinzena/Mês/Trimestre),
# aplicadas sobre ``criado_em``.
_PERIODOS_SOLICITACAO = {
    "dia": "criado_em::date = current_date",
    "quinzena": "criado_em >= now() - interval '15 days'",
    "mes": "date_trunc('month', criado_em) = date_trunc('month', now())",
    "trimestre": (
        "date_trunc('quarter', criado_em) = date_trunc('quarter', now())"
    ),
}


def _solicitacoes_por_periodo(origem: str, status_counts: str) -> str:
    """Monta o UNION ALL das contagens por período (uma linha por período).

    ``origem`` é a tabela (ou subquery com alias) que expõe ``status`` e
    ``criado_em``; ``status_counts`` são as expressões ``count(*) filter``
    específicas do tipo de solicitação.
    """
    blocos = [
        f"select '{periodo}' as periodo,{status_counts}"
        f"\nfrom {origem}\nwhere {condicao}"
        for periodo, condicao in _PERIODOS_SOLICITACAO.items()
    ]
    return "\nunion all\n".join(blocos)


_DIETA_STATUS_COUNTS = """
    count(*) as total,
    count(*) filter (where status = 'CODAE_AUTORIZADO') as autorizadas,
    count(*) filter (where status = 'CODAE_A_AUTORIZAR') as aguardando,
    count(*) filter (where status = 'CODAE_NEGOU_PEDIDO') as negadas,
    count(*) filter (where status in (
        'ESCOLA_CANCELOU',
        'CANCELADO_ALUNO_NAO_PERTENCE_REDE',
        'TERMINADA_AUTOMATICAMENTE_SISTEMA'
    )) as canceladas
"""

SOLICITACOES_DIETAS_ESPECIAIS = _solicitacoes_por_periodo(
    "dieta_especial_solicitacaodietaespecial", _DIETA_STATUS_COUNTS
)


# Solicitações de alimentação: inclusão, alteração de cardápio, suspensão,
# inversão e kit lanche. Cada uma é uma tabela própria; todas expõem
# ``status`` (workflow PedidoAPartirDaEscola / Informativo) e uma data de
# criação. As de kit lanche guardam ``criado_em`` na OneToOne
# ``kit_lanche_solicitacaokitlanche`` (via ``solicitacao_kit_lanche_id``).
_ALIMENTACAO_TABELAS_DIRETAS = (
    "cardapio_alteracaocardapio",
    "cardapio_alteracaocardapiocei",
    "cardapio_alteracaocardapiocemei",
    "cardapio_gruposuspensaoalimentacao",
    "cardapio_inversaocardapio",
    "cardapio_suspensaoalimentacaodacei",
    "inclusao_alimentacao_grupoinclusaoalimentacaonormal",
    "inclusao_alimentacao_inclusaoalimentacaocontinua",
    "inclusao_alimentacao_inclusaoalimentacaodacei",
    "inclusao_alimentacao_inclusaodealimentacaocemei",
    "kit_lanche_solicitacaokitlanchecemei",
)
_ALIMENTACAO_TABELAS_KIT_LANCHE = (
    "kit_lanche_solicitacaokitlancheavulsa",
    "kit_lanche_solicitacaokitlancheceiavulsa",
    "kit_lanche_solicitacaokitlancheunificada",
)


def _origem_alimentacoes() -> str:
    """Une (status, criado_em) de todas as solicitações de alimentação."""
    # Nomes de tabela são constantes internas (não entram por input),
    # então o alerta de SQL injection do ruff (S608) não se aplica.
    diretas = [
        f"select status, criado_em from {tabela}"  # noqa: S608
        for tabela in _ALIMENTACAO_TABELAS_DIRETAS
    ]
    kit_lanche = [
        f"select w.status, s.criado_em from {tabela} w"  # noqa: S608
        " join kit_lanche_solicitacaokitlanche s"
        " on s.id = w.solicitacao_kit_lanche_id"
        for tabela in _ALIMENTACAO_TABELAS_KIT_LANCHE
    ]
    return "(\n" + "\nunion all\n".join(diretas + kit_lanche) + "\n) sa"


_ALIMENTACAO_STATUS_COUNTS = """
    count(*) filter (where status <> 'RASCUNHO') as total,
    count(*) filter (where status in (
        'CODAE_AUTORIZADO',
        'TERCEIRIZADA_TOMOU_CIENCIA',
        'INFORMADO'
    )) as autorizadas,
    count(*) filter (where status in (
        'DRE_A_VALIDAR',
        'DRE_VALIDADO',
        'DRE_PEDIU_ESCOLA_REVISAR',
        'CODAE_QUESTIONADO',
        'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'
    )) as aguardando,
    count(*) filter (where status in (
        'CODAE_NEGOU_PEDIDO',
        'DRE_NAO_VALIDOU_PEDIDO_ESCOLA'
    )) as negadas,
    count(*) filter (where status in (
        'ESCOLA_CANCELOU',
        'CANCELADO_AUTOMATICAMENTE',
        'TERMINADA_AUTOMATICAMENTE_SISTEMA'
    )) as canceladas
"""

SOLICITACOES_ALIMENTACOES = _solicitacoes_por_periodo(
    _origem_alimentacoes(), _ALIMENTACAO_STATUS_COUNTS
)


# --- Logística (pré-recebimento) ---

# Cronograma de entregas (workflow CronogramaWorkflow). "Aprovadas" é o
# estado final ASSINADO_CODAE; "enviadas" quando vai ao fornecedor; as
# demais assinaturas/alterações em curso contam como "aguardando".
CRONOGRAMAS_ENTREGAS = """
select
    count(*) filter (where status in (
        'ALTERACAO_CODAE',
        'SOLICITADO_ALTERACAO',
        'ASSINADO_FORNECEDOR',
        'ASSINADO_DILOG_ABASTECIMENTO'
    )) as aguardando,
    count(*) filter (where status = 'ASSINADO_E_ENVIADO_AO_FORNECEDOR')
        as enviadas,
    count(*) filter (where status = 'ASSINADO_CODAE') as aprovadas
from pre_recebimento_cronograma
"""

# Ficha técnica do produto (workflow FichaTecnicaDoProdutoWorkflow).
FICHAS_TECNICAS_PRODUTOS = """
select
    count(*) as cadastradas,
    count(*) filter (where status = 'APROVADA') as aprovadas,
    count(*) filter (where status = 'ENVIADA_PARA_ANALISE') as em_analise,
    count(*) filter (where status = 'ENVIADA_PARA_CORRECAO')
        as pendentes_correcao
from pre_recebimento_fichatecnicadoproduto
"""

# Layout de embalagem (workflow LayoutDeEmbalagemWorkflow).
LAYOUTS_EMBALAGENS = """
select
    count(*) as cadastrados,
    count(*) filter (where status = 'APROVADO') as aprovados,
    count(*) filter (where status = 'ENVIADO_PARA_ANALISE')
        as aguardando_codae,
    count(*) filter (where status = 'SOLICITADO_CORRECAO')
        as pendentes_correcao
from pre_recebimento_layoutdeembalagem
"""

# Fornecedores e distribuidores: terceirizadas cujo tipo_servico é de
# fornecimento/distribuição (as de alimentação usam TERCEIRIZADA).
FORNECEDORES_DISTRIBUIDORES = """
select
    count(*) as cadastradas,
    count(*) filter (where ativo) as ativas
from terceirizada_terceirizada
where tipo_servico in (
    'FORNECEDOR',
    'FORNECEDOR_E_DISTRIBUIDOR',
    'DISTRIBUIDOR_ARMAZEM'
)
"""
