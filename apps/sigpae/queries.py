"""Consultas SQL de leitura no banco do SIGPAE."""

USUARIOS_ACESSO_ATIVO = """
select
    count(*) filter (where last_login is not null) as total,
    count(*) filter (where last_login >= now() - interval '30 days')
        as ativos_30_dias
from perfil_usuario
where is_active
"""

USUARIOS_POR_TIPO_PERFIL = """
select pp.visao, count(distinct pv.usuario_id) as total_usuarios
from perfil_vinculo pv
join perfil_perfil pp on pp.id = pv.perfil_id
where pv.ativo
group by pp.visao
"""
