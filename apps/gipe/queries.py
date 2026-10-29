"""Consultas SQL de leitura nos três bancos do GIPE.

Levantadas no discovery de contrato do GIPE (AB#156989). São três bancos
sem FK entre si:

- ocorrências (MS de intercorrências);
- anexos (MS de anexos, ligado à ocorrência só pelo UUID);
- usuários e unidades (``SME-Gipe-Backend``).

A ocorrência só guarda códigos EOL e o RF do analista; os nomes saem de
uma segunda consulta no banco de usuários, cruzada no ``handler``.

Parâmetros nomeados: ``inicio`` e ``fim`` (``date``, ano letivo com fim
exclusivo), ``codigos`` e ``usernames`` (listas de texto). O cast
explícito (``::date``, ``::text[]``) segue o padrão do ``sigescola``.
"""

# Recorte por ano letivo na data da ocorrência (alias ``i``).
_FILTRO_ANO = """
    i.data_ocorrencia >= %(inicio)s::date
    and i.data_ocorrencia < %(fim)s::date
"""

# Dias corridos entre a criação e um marco de finalização.
_DIAS_RESOLUCAO = "extract(epoch from (i.finalizado_gipe_em - i.criado_em))"
_DIAS_TRATATIVA = "extract(epoch from (i.finalizado_diretor_em - i.criado_em))"

# Estágios de encaminhamento concluídos (diretor, DRE e GIPE).
_ETAPAS_CONCLUIDAS = """
    (i.finalizado_diretor_em is not null)::int
    + (i.finalizado_dre_em is not null)::int
    + (i.finalizado_gipe_em is not null)::int
"""

# --- Banco de ocorrências -------------------------------------------------

# "Abertas" = em_preenchimento_diretor ("Incompleta" no GIPE).
STATUS_GERAL = f"""
select
    count(*) as cadastrados,
    count(*) filter (where i.status = 'em_preenchimento_diretor')
        as abertas,
    count(*) filter (
        where i.status in ('enviado_para_dre', 'enviado_para_gipe')
    ) as em_andamento,
    count(*) filter (where i.status = 'finalizada') as finalizadas
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
"""  # noqa: S608

# Resolução = criação até a finalização pelo GIPE (fim do ciclo). Primeira
# tratativa = criação até a finalização pelo diretor (aproximação, ainda
# sem confirmação do GIPE). O valor é do ano letivo; as janelas de 30 dias
# (para a tendência) são relativas a hoje.
TEMPO_RESPOSTA = f"""
select
    avg({_DIAS_RESOLUCAO} / 86400.0) filter (
        where i.finalizado_gipe_em is not null and {_FILTRO_ANO}
    ) as resolucao,
    avg({_DIAS_RESOLUCAO} / 86400.0) filter (
        where i.finalizado_gipe_em >= now() - interval '30 days'
    ) as resolucao_30d,
    avg({_DIAS_RESOLUCAO} / 86400.0) filter (
        where i.finalizado_gipe_em >= now() - interval '60 days'
            and i.finalizado_gipe_em < now() - interval '30 days'
    ) as resolucao_30d_anterior,
    avg({_DIAS_TRATATIVA} / 86400.0) filter (
        where i.finalizado_diretor_em is not null and {_FILTRO_ANO}
    ) as tratativa,
    avg({_DIAS_TRATATIVA} / 86400.0) filter (
        where i.finalizado_diretor_em >= now() - interval '30 days'
    ) as tratativa_30d,
    avg({_DIAS_TRATATIVA} / 86400.0) filter (
        where i.finalizado_diretor_em >= now() - interval '60 days'
            and i.finalizado_diretor_em < now() - interval '30 days'
    ) as tratativa_30d_anterior
from intercorrencias_intercorrencia i
"""  # noqa: S608

# Fotografia do momento, sem recorte de ano.
SEM_MOVIMENTACAO_7_DIAS = """
select count(*) as total
from intercorrencias_intercorrencia i
where i.status <> 'finalizada'
    and i.atualizado_em < now() - interval '7 days'
"""

# Movimentações = criação + cada estágio concluído. "encaminhamentos" é a
# soma dos estágios concluídos; a média conta a criação (teto 4,0).
MOVIMENTACOES = f"""
select
    count(*) as ocorrencias,
    coalesce(sum({_ETAPAS_CONCLUIDAS}), 0) as encaminhamentos,
    avg(1 + {_ETAPAS_CONCLUIDAS}) as media_por_ocorrencia
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
"""  # noqa: S608

POR_DRE = f"""
select i.dre_codigo_eol as codigo, count(*) as total
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
group by 1
"""  # noqa: S608

POR_UE = f"""
select i.unidade_codigo_eol as codigo, count(*) as total
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
group by 1
"""  # noqa: S608

# Patrimonial x interpessoal é o booleano da ocorrência, não o tipo.
POR_CATEGORIA = f"""
select
    count(*) filter (where i.sobre_furto_roubo_invasao_depredacao)
        as patrimoniais,
    count(*) filter (where not i.sobre_furto_roubo_invasao_depredacao)
        as interpessoais
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
"""  # noqa: S608

POR_TIPO = f"""
select
    i.sobre_furto_roubo_invasao_depredacao as patrimonial,
    t.nome,
    count(*) as total
from intercorrencias_intercorrencia_tipos_ocorrencia it
join intercorrencias_tipoocorrencia t on t.id = it.tipoocorrencia_id
join intercorrencias_intercorrencia i on i.id = it.intercorrencia_id
where {_FILTRO_ANO}
group by 1, 2
"""  # noqa: S608

POR_MES = f"""
select date_trunc('month', i.data_ocorrencia)::date as mes, count(*) as total
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
group by 1
order by 1
"""  # noqa: S608

# Não há calendário letivo oficial: corte fixo por mês, aprovado pelo GIPE
# como solução provisória.
POR_BIMESTRE = f"""
select
    case
        when extract(month from i.data_ocorrencia) between 2 and 4 then 1
        when extract(month from i.data_ocorrencia) between 5 and 7 then 2
        when extract(month from i.data_ocorrencia) between 8 and 9 then 3
        else 4
    end as bimestre,
    count(*) as total
from intercorrencias_intercorrencia i
where {_FILTRO_ANO}
group by 1
order by 1
"""  # noqa: S608

# ``finalizado_gipe_por`` é o RF (username) do analista.
TRATADAS_POR_ANALISTA = f"""
select
    i.finalizado_gipe_por as username,
    count(*) as ocorrencias_tratadas,
    avg({_DIAS_RESOLUCAO} / 86400.0) as tempo_medio_dias
from intercorrencias_intercorrencia i
where i.finalizado_gipe_em is not null
    and i.finalizado_gipe_por <> ''
    and {_FILTRO_ANO}
group by 1
"""  # noqa: S608

TRATADAS_POR_DRE = f"""
select i.dre_codigo_eol as codigo, count(*) as total
from intercorrencias_intercorrencia i
where i.finalizado_gipe_em is not null
    and {_FILTRO_ANO}
group by 1
"""  # noqa: S608

# --- Banco de anexos ------------------------------------------------------

# Fotografia do momento, sem recorte de ano. ``ativo = false`` é exclusão
# lógica do anexo.
ANEXOS_ENVIADOS = """
select count(*) as total
from anexos_anexo
where ativo
"""

# --- Banco de usuários ----------------------------------------------------

# ``last_login`` guarda só o último login (sem histórico): dá para contar
# usuários, não acessos.
KPIS_USUARIOS = """
select
    count(*) filter (where is_active) as cadastrados,
    count(*) filter (
        where is_active and last_login >= now() - interval '30 days'
    ) as com_acesso_ativo,
    count(*) filter (where date_joined >= now() - interval '30 days')
        as novos_30_dias,
    count(*) filter (where last_login >= date_trunc('day', now()))
        as unicos_hoje
from users_user
"""

UNIDADES_POR_CODIGO = """
select codigo_eol as codigo, nome
from unidades_unidade
where codigo_eol = any(%(codigos)s::text[])
"""

NOMES_POR_USERNAME = """
select username, name as nome
from users_user
where username = any(%(usernames)s::text[])
"""

# Os 6 perfis do painel vêm de cargo x ``is_app_admin``, não de 6 cargos.
USUARIOS_POR_PERFIL = """
select c.nome as cargo, u.is_app_admin as admin, count(*) as total
from users_user u
join users_cargo c on c.codigo = u.cargo_id
where u.is_active
group by 1, 2
"""

# DRE do usuário: a DRE da unidade vinculada, ou a própria unidade quando
# ela já é uma DRE.
USUARIOS_POR_DRE = """
select
    coalesce(un.dre_id, un.codigo_eol) as codigo,
    d.nome,
    count(distinct uu.user_id) as total
from users_user_unidades uu
join users_user u on u.id = uu.user_id and u.is_active
join unidades_unidade un on un.codigo_eol = uu.unidade_id
left join unidades_unidade d
    on d.codigo_eol = coalesce(un.dre_id, un.codigo_eol)
group by 1, 2
"""

USUARIOS_POR_UE = """
select un.codigo_eol as codigo, un.nome, count(distinct uu.user_id) as total
from users_user_unidades uu
join users_user u on u.id = uu.user_id and u.is_active
join unidades_unidade un on un.codigo_eol = uu.unidade_id
where un.tipo_unidade <> 'DRE'
group by 1, 2
"""
