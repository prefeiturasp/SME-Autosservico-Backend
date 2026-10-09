"""Consultas SQL de leitura no banco MySQL do Intranet.

Queries levantadas e validadas no QA no discovery de contrato do Intranet
(prefixo de tabela ``int_``). Sorteios (``post_type = 'post'``) e Ordem de
Inscrição (``post_type = 'cortesias'``) têm tabelas próprias, por isso cada
indicador tem uma query por sistema.

O ``pymysql`` sempre formata a query com ``%``, então ``%`` literal é
escrito como ``%%``. As queries com recorte de data usam os parâmetros
nomeados ``inicio`` e ``fim`` (qualquer um pode ser ``None`` = sem limite).

Os agrupamentos devolvem códigos crus (``tipo_evento``, ganhador, ``dre``);
os rótulos exibidos no painel ficam em ``mapper.py``.
"""

# Mesmo filtro de período para as duas tabelas de inscrição.
_FILTRO_PERIODO = """
    and (%(inicio)s is null or i.data_inscricao >= %(inicio)s)
    and (%(fim)s is null or i.data_inscricao < %(fim)s)
"""

# ``wp_last_login`` é um timestamp Unix por usuário, sobrescrito a cada
# login (sem histórico): só dá para contar usuários, não acessos.
KPIS_USUARIOS = """
select
    (select count(distinct u.ID)
        from int_users u
        join int_usermeta um
            on um.user_id = u.ID and um.meta_key = 'wp_last_login'
        where um.meta_value >= unix_timestamp(now() - interval 30 day)
    ) as com_acesso_ativo,
    (select count(distinct u.ID)
        from int_users u
        join int_usermeta um
            on um.user_id = u.ID and um.meta_key = 'wp_last_login'
        where um.meta_value >= unix_timestamp(curdate())
    ) as unicos_hoje
"""

# "Realizado" = pelo menos uma inscrição sorteada. Os demais são ativos ou
# encerrados pela data ``enc_inscri`` (ACF, string ``Ymd`` sem separador).
SORTEIOS_STATUS_GERAL = """
select
    count(distinct p.ID) as cadastrados,
    sum(case when r.tem_sorteado = 1 then 1 else 0 end) as realizados,
    sum(case when (r.tem_sorteado is null or r.tem_sorteado = 0)
        and enc.meta_value >= date_format(curdate(), '%%Y%%m%%d')
        then 1 else 0 end) as ativos,
    sum(case when (r.tem_sorteado is null or r.tem_sorteado = 0)
        and enc.meta_value < date_format(curdate(), '%%Y%%m%%d')
        then 1 else 0 end) as encerrados
from int_posts p
left join int_postmeta enc
    on enc.post_id = p.ID and enc.meta_key = 'enc_inscri'
left join (
    select post_id, max(sorteado) as tem_sorteado
    from int_inscricoes
    group by post_id
) r on r.post_id = p.ID
where p.post_type = 'post'
    and p.post_status = 'publish'
"""

# Ordem de Inscrição não tem "realizado" (é ordem de chegada). Aqui a data
# de encerramento é ``DATE`` nativo, sem conversão.
ORDEM_STATUS_GERAL = """
select
    count(distinct p.ID) as cadastrados,
    sum(case when d.encerramento_max >= curdate() then 1 else 0 end)
        as ativos,
    sum(case when d.encerramento_max < curdate() then 1 else 0 end)
        as encerrados
from int_posts p
join (
    select post_id, max(encerramento_inscricoes) as encerramento_max
    from int_cortesias_acf_datas
    group by post_id
) d on d.post_id = p.ID
where p.post_type = 'cortesias'
    and p.post_status = 'publish'
"""

# ``left join`` em ``tipo_evento``: posts sem o campo ACF entram com
# ``tipo_evento`` nulo (bucket "Não informado") em vez de serem descartados,
# para os totais de tipo/ganhador/DRE fecharem entre si.
SORTEIOS_POR_TIPO = f"""
select pm.meta_value as tipo_evento, count(*) as total
from int_inscricoes i
join int_posts p on p.ID = i.post_id
left join int_postmeta pm
    on pm.post_id = p.ID and pm.meta_key = 'tipo_evento'
where p.post_type = 'post'
    {_FILTRO_PERIODO}
group by pm.meta_value
"""  # noqa: S608

ORDEM_POR_TIPO = f"""
select pm.meta_value as tipo_evento, count(*) as total
from int_cortesias_inscricoes i
join int_posts p on p.ID = i.post_id
left join int_postmeta pm
    on pm.post_id = p.ID and pm.meta_key = 'tipo_evento'
where p.post_type = 'cortesias'
    {_FILTRO_PERIODO}
group by pm.meta_value
"""  # noqa: S608

# Estagiário = inscrição com programa de estágio; parceiro = usermeta
# ``parceira = 1``; os demais são servidores.
_CASE_GANHADOR = """
    case
        when i.programa_estagio is not null then 'estagiario'
        when um.meta_value = '1' then 'parceiro'
        else 'servidor'
    end
"""

SORTEIOS_POR_GANHADOR = f"""
select {_CASE_GANHADOR} as ganhador, count(*) as total
from int_inscricoes i
join int_posts p on p.ID = i.post_id
left join int_usermeta um
    on um.user_id = i.user_id and um.meta_key = 'parceira'
where p.post_type = 'post'
    {_FILTRO_PERIODO}
group by ganhador
"""  # noqa: S608

ORDEM_POR_GANHADOR = f"""
select {_CASE_GANHADOR} as ganhador, count(*) as total
from int_cortesias_inscricoes i
join int_posts p on p.ID = i.post_id
left join int_usermeta um
    on um.user_id = i.user_id and um.meta_key = 'parceira'
where p.post_type = 'cortesias'
    {_FILTRO_PERIODO}
group by ganhador
"""  # noqa: S608

# ``dre`` é texto livre, sem FK para unidades: vai como veio do banco.
SORTEIOS_POR_DRE = f"""
select i.dre as dre, count(*) as total
from int_inscricoes i
join int_posts p on p.ID = i.post_id
where p.post_type = 'post'
    {_FILTRO_PERIODO}
group by i.dre
"""  # noqa: S608

ORDEM_POR_DRE = f"""
select i.dre as dre, count(*) as total
from int_cortesias_inscricoes i
join int_posts p on p.ID = i.post_id
where p.post_type = 'cortesias'
    {_FILTRO_PERIODO}
group by i.dre
"""  # noqa: S608

# CVs só finalizados e oportunidades só publicadas (confirmado com o time
# do Intranet). "Contratação efetivada" = inscrição com status aprovado.
OPORTUNIDADES_STATUS_GERAL = """
select
    (select count(*) from int_posts
        where post_type = 'oportunidade' and post_status = 'publish'
    ) as oportunidades_cadastradas,
    (select count(*) from int_banco_talentos
        where status_curriculo = 'finalizado'
    ) as cvs_cadastrados,
    (select count(*) from int_oportunidade_inscricoes)
        as inscricoes_realizadas,
    (select count(*) from int_oportunidade_inscricoes
        where status = 'aprovado'
    ) as contratacoes_efetivadas
"""
