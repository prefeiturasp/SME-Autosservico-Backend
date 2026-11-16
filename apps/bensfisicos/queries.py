"""Consultas SQL de leitura no banco do Bens Físicos.

Levantadas e validadas em homologação no discovery de contrato do Bens
Físicos (AB#158715). Os indicadores são a fotografia do momento, sem
recorte de período.
"""

USUARIOS_ATIVOS = """
select count(*) as com_acesso_ativo
from usuario_usuario
where is_active
    and last_login >= now() - interval '30 days'
"""

# Sem histórico de login: "únicos por dia" é aproximado pela atividade
# registrada (alterações, status, cadastros, movimentações, baixas e admin).
USUARIOS_UNICOS = """
with atividade as (
    select alterado_por_id as usuario_id, alterado_em as momento
    from dados_comuns_historicogeral
    union all
    select atualizado_por_id, atualizado_em
    from bem_patrimonial_statusbempatrimonial
    union all
    select criado_por_id, criado_em from bem_patrimonial_bempatrimonial
    union all
    select solicitado_por_id, criado_em
    from bem_patrimonial_movimentacaobempatrimonial
    union all
    select criado_por_id, data_criacao
    from bem_patrimonial_baixafisicabempatrimonial
    union all
    select user_id, action_time from django_admin_log
)
select
    count(distinct usuario_id) filter (where momento >= current_date)
        as unicos_hoje,
    count(distinct (usuario_id, momento::date))
        filter (where momento < current_date) / 30.0 as media_diaria_30_dias
from atividade
where usuario_id is not null
    and momento >= current_date - 30
"""

BENS = """
select
    count(*) as bens_cadastrados,
    count(*) filter (where status = 'aguardando_aprovacao')
        as aguardando_aprovacao
from bem_patrimonial_bempatrimonial
where not excluido
"""

BENS_POR_UNIDADE = """
select ua.sigla, ua.nome, count(*) as bens
from bem_patrimonial_bempatrimonial b
join dados_comuns_unidadeadministrativa ua
    on ua.id = b.unidade_administrativa_id
where not b.excluido
group by ua.id, ua.sigla, ua.nome
order by bens desc
"""

# Baixas em elaboração (aguardando_envio) ainda não foram enviadas.
BAIXAS_FISICAS = """
select
    count(*) filter (where status = 'aceita') as aprovadas,
    count(*) filter (where status = 'solicitada') as aguardando_aprovacao
from bem_patrimonial_baixafisicabempatrimonial
"""

MOVIMENTACOES = """
select
    count(*) filter (where status = 'aceita') as realizadas,
    count(*) filter (where status = 'enviada') as pendentes
from bem_patrimonial_movimentacaobempatrimonial
"""

# A transferência é efetivada de uma vez e recebe o número da NTBPM.
TRANSFERENCIAS = """
select count(*) as transferencias_realizadas
from bem_patrimonial_transferenciabempatrimonial
where coalesce(numero_ntbpm, '') <> ''
"""
