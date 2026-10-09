"""Consultas SQL de leitura no banco do SIG-Escola (PTRF, ``db_ptrf``).

Levantadas no discovery de contrato (AB#156992) e revalidadas no banco
atual em 09/10/2026. Os parâmetros são nomeados:

- ``inicio`` e ``fim`` (``date``): janela do filtro. Em modo período é a
  janela de despesas do ``core_periodo``; em modo intervalo, as datas
  escolhidas na tela. O serviço sempre preenche os dois.
- ``dre`` e ``ue`` (código EOL, texto): recorte por unidade; ``None``
  não filtra.

Os blocos ligados a ``core_periodo`` (prestações, repasses, devoluções e
demonstrativos) pegam todos os períodos do PTRF que cruzam a janela. Só
entra o recurso PTRF (``core_recurso.legado``), porque a referência do
período (``2026.1``) se repete entre recursos.

O ``%(nome)s::tipo`` tem cast explícito porque o psycopg 3 manda o
parâmetro para o servidor, e um ``null`` sem tipo não resolve no
``is null``.
"""

# Recorte por DRE/UE a partir da unidade (alias ``u``) da associação.
_FILTRO_UNIDADE = """
    and (%(dre)s::text is null or u.dre_id = %(dre)s::text)
    and (%(ue)s::text is null or u.codigo_eol = %(ue)s::text)
"""

# Períodos do PTRF (alias ``p``) que cruzam a janela. O período corrente
# ainda não tem fim (``data_fim_realizacao_despesas`` nulo).
_PERIODO_NA_JANELA = """
    p.recurso_id in (select id from core_recurso where legado)
    and p.data_inicio_realizacao_despesas <= %(fim)s::date
    and coalesce(p.data_fim_realizacao_despesas, 'infinity')
        >= %(inicio)s::date
"""

PERIODOS = """
select
    p.referencia,
    p.data_inicio_realizacao_despesas as data_inicio,
    p.data_fim_realizacao_despesas as data_fim
from core_periodo p
where p.recurso_id in (select id from core_recurso where legado)
order by p.data_inicio_realizacao_despesas desc
"""

# UEs (com associação) de uma DRE, para o select de UE da tela.
UNIDADES_DA_DRE = """
select u.codigo_eol, u.tipo_unidade, u.nome
from core_unidade u
where u.dre_id = %(dre)s::text
    and exists (
        select 1 from core_associacao a where a.unidade_id = u.codigo_eol
    )
order by u.nome
"""

# Fotografia global, sem filtro. total = já logaram (regra do SGP);
# novos_30_dias = cadastrados nos últimos 30 dias (regra do SERAp
# Estudantes), para o texto "N novos nos últimos 30 dias".
USUARIOS_ACESSO_ATIVO = """
select
    count(*) filter (where last_login is not null) as total,
    count(*) filter (where date_joined >= now() - interval '30 days')
        as novos_30_dias
from users_user
"""

# Log de login: o auditlog grava cada atualização de ``last_login`` em
# ``users.user``. Hoje: usuários únicos e acessos. Nos 30 dias anteriores a
# hoje: pares (usuário, dia) e acessos, para as médias diárias. Fotografia
# global, sem filtro.
USUARIOS_LOGINS = """
with logins as (
    select l.object_pk as usuario, l."timestamp" as momento
    from auditlog_logentry l
    join django_content_type ct on ct.id = l.content_type_id
    where ct.app_label = 'users'
        and ct.model = 'user'
        and l.action = 1
        and l."timestamp" >= current_date - interval '30 days'
        and strpos(l.changes::text, '"last_login"') > 0
)
select
    count(distinct usuario) filter (where momento >= current_date)
        as unicos_hoje,
    count(*) filter (where momento >= current_date) as acessos_hoje,
    count(distinct (usuario, momento::date))
        filter (where momento < current_date) as usuarios_dia_30_dias,
    count(*) filter (where momento < current_date) as acessos_30_dias
from logins
"""

# Fotografia: associações não encerradas, sem recorte de data.
UES_APTAS = f"""
select count(*) as total
from core_associacao a
join core_unidade u on u.codigo_eol = a.unidade_id
where a.data_de_encerramento is null
    {_FILTRO_UNIDADE}
"""  # noqa: S608

PRESTACOES_POR_STATUS = f"""
select pc.status as situacao, count(*) as quantidade
from core_prestacaoconta pc
join core_periodo p on p.id = pc.periodo_id
join core_associacao a on a.id = pc.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where {_PERIODO_NA_JANELA}
    {_FILTRO_UNIDADE}
group by pc.status
"""  # noqa: S608

# Repasses do período (previsto: capital + custeio + livre).
CREDITOS_DISPONIVEIS = f"""
select coalesce(sum(
    coalesce(r.valor_capital, 0)
    + coalesce(r.valor_custeio, 0)
    + coalesce(r.valor_livre, 0)
), 0) as valor
from receitas_repasse r
join core_periodo p on p.id = r.periodo_id
join core_associacao a on a.id = r.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where {_PERIODO_NA_JANELA}
    {_FILTRO_UNIDADE}
"""  # noqa: S608

# A despesa não tem período: usa a data da transação dentro da janela.
DESPESAS_REGISTRADAS = f"""
select coalesce(sum(d.valor_total), 0) as valor
from despesas_despesa d
join core_associacao a on a.id = d.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where d.status <> 'INATIVO'
    and d.recurso_id in (select id from core_recurso where legado)
    and d.data_transacao between %(inicio)s::date and %(fim)s::date
    {_FILTRO_UNIDADE}
"""  # noqa: S608

# Só a versão FINAL: o banco atual também guarda as prévias.
DEMONSTRATIVOS_GERADOS = f"""
select count(*) as total
from core_demonstrativofinanceiro df
join core_prestacaoconta pc on pc.id = df.prestacao_conta_id
join core_periodo p on p.id = pc.periodo_id
join core_associacao a on a.id = pc.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where df.status = 'CONCLUIDO'
    and df.versao = 'FINAL'
    and {_PERIODO_NA_JANELA}
    {_FILTRO_UNIDADE}
"""  # noqa: S608

DEVOLUCAO_AO_TESOURO = f"""
select coalesce(sum(dt.valor), 0) as valor
from core_devolucaoaotesouro dt
join core_prestacaoconta pc on pc.id = dt.prestacao_conta_id
join core_periodo p on p.id = pc.periodo_id
join core_associacao a on a.id = pc.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where {_PERIODO_NA_JANELA}
    {_FILTRO_UNIDADE}
"""  # noqa: S608

# Critério do discovery: rateios CAPITAL das despesas da janela, sem os
# inativos e os marcados para não sair na relação de bens.
BENS_PRODUZIDOS = f"""
select
    coalesce(sum(r.quantidade_itens_capital), 0) as quantidade,
    coalesce(sum(r.valor_rateio), 0) as valor
from despesas_rateiodespesa r
join despesas_despesa d on d.id = r.despesa_id
join core_associacao a on a.id = d.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where r.aplicacao_recurso = 'CAPITAL'
    and r.status <> 'INATIVO'
    and coalesce(r.nao_exibir_em_rel_bens, false) = false
    and d.recurso_id in (select id from core_recurso where legado)
    and d.data_transacao between %(inicio)s::date and %(fim)s::date
    {_FILTRO_UNIDADE}
"""  # noqa: S608

# PAAs cujo período de PAA cruza a janela, por status.
PAA_POR_STATUS = f"""
select pa.status as situacao, count(*) as quantidade
from paa_paa pa
join paa_periodopaa pp on pp.id = pa.periodo_paa_id
join core_associacao a on a.id = pa.associacao_id
join core_unidade u on u.codigo_eol = a.unidade_id
where pp.data_inicial <= %(fim)s::date
    and pp.data_final >= %(inicio)s::date
    {_FILTRO_UNIDADE}
group by pa.status
"""  # noqa: S608
