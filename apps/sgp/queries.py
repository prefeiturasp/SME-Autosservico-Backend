"""Consultas SQL de leitura no banco do SGP.

Queries reais de produção do NovoSGP, levantadas no discovery de
contrato (AB#154278). Os parâmetros são posicionais (``%s``) na ordem
``(ano_letivo, bimestre)`` — ou apenas ``(ano_letivo,)`` quando indicado.
"""

USUARIOS_ACESSO_ATIVO = """
select
    count(*) filter (where ultimo_login is not null) as total,
    count(*) filter (where ultimo_login >= now() - interval '30 days')
        as ativos_30_dias
from usuario
"""

USUARIOS_DE_UNIDADES = """
select
    count(distinct usuario_id) as total,
    count(distinct dre_id) as diretorias
from abrangencia
where ue_id is not null
"""

FECHAMENTO_POR_SITUACAO = """
select
    case when cfct.status in (0, 1) then 0 else cfct.status end as situacao,
    count(cfct.id) as quantidade
from consolidado_fechamento_componente_turma cfct
inner join turma t on t.id = cfct.turma_id
where t.tipo_turma in (1, 2, 7)
    and t.ano_letivo = %s
    and cfct.bimestre = %s
group by 1
"""

CONSELHO_CLASSE_POR_SITUACAO = """
select cccat.status as situacao,
    count(distinct cccat.aluno_codigo) as quantidade
from consolidado_conselho_classe_aluno_turma cccat
inner join consolidado_conselho_classe_aluno_turma_nota cccatn
    on cccatn.consolidado_conselho_classe_aluno_turma_id = cccat.id
inner join conselho_classe_aluno cca
    on cca.aluno_codigo = cccat.aluno_codigo
inner join conselho_classe cc on cc.id = cca.conselho_classe_id
inner join fechamento_turma ft on ft.id = cc.fechamento_turma_id
inner join turma t on t.id = ft.turma_id and cccat.turma_id = t.id
where t.tipo_turma = 1
    and t.ano_letivo = %s
    and coalesce(cccatn.bimestre, 0) = %s
    and not cccat.excluido
group by cccat.status
"""

# Fonte de "alunos ativos na turma" para calcular o bucket
# "não iniciados" do conselho de classe. Aproximação de trabalho
# (situacaomatricula = 'Ativo'), não confirmada formalmente pelo SGP.
CONSELHO_CLASSE_ALUNOS_ATIVOS = """
select count(distinct at.codigoaluno) as alunos_ativos
from extracao.alunos_turmas at
join turma t on t.turma_id = at.codigoturma
where at.situacaomatricula = 'Ativo'
    and t.ano_letivo = %s
    and t.tipo_turma = 1
"""
