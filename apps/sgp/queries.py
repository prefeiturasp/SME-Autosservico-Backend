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

# Sondagens de escrita realizadas x esperadas, por ano letivo e bimestre.
# "esperadas" = total de alunos com sondagem prevista; "realizadas" = os
# que têm nível preenchido (total menos os sem preenchimento).
SONDAGENS_REALIZADAS_ESPERADAS = """
select
    coalesce(sum(quantidade_aluno), 0) as esperadas,
    coalesce(
        sum(quantidade_aluno - coalesce(sem_preenchimento, 0)), 0
    ) as realizadas
from painel_educacional_consolidacao_sondagem_escrita_ue
where ano_letivo = %s and bimestre = %s
"""

# Frequências lançadas x esperadas, por ano letivo e bimestre. Usa a
# consolidação por turma/bimestre (tipo_consolidacao = 1): total_aulas são
# as esperadas e total_frequencias as lançadas. O bimestre vem de
# periodo_escolar, casando o calendário da turma pela modalidade
# (modalidade_codigo do EOL -> modalidade do tipo de calendário:
# 1=Infantil, 3=EJA, demais=Fundamental/Médio) e pela data de início do
# período de consolidação dentro da janela do bimestre.
FREQUENCIAS_LANCADAS_ESPERADAS = """
select
    coalesce(sum(cft.total_aulas), 0) as esperadas,
    coalesce(sum(cft.total_frequencias), 0) as lancadas
from consolidacao_frequencia_turma cft
join turma t on t.id = cft.turma_id
join tipo_calendario tc
    on tc.ano_letivo = t.ano_letivo
    and not tc.excluido
    and tc.modalidade = case t.modalidade_codigo
        when 1 then 3
        when 3 then 2
        else 1
    end
join periodo_escolar pe
    on pe.tipo_calendario_id = tc.id
    and cft.periodo_inicio >= pe.periodo_inicio
    and cft.periodo_inicio <= pe.periodo_fim
where cft.tipo_consolidacao = 1
    and t.ano_letivo = %s
    and t.tipo_turma in (1, 2, 7)
    and pe.bimestre = %s
"""
