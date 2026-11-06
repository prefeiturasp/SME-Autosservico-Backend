"""Consultas SQL de leitura no banco do SGP.

Queries reais de produção do NovoSGP, levantadas no discovery de
contrato (AB#154278 e AB#159683). Usuários, frequências e sondagens usam
parâmetros posicionais ``(ano_letivo, bimestre)``; as consultas por
segmento usam ``Periodo.parametros``.
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

# Segmento pela modalidade da turma: 3 = EJA (filtra o semestre também),
# 5 = Fundamental e 6 = Médio. Vai como parâmetro pra não montar SQL com
# string. A sigla da DRE ("DRE - BT" -> "BT") segue a regra do SGP.

FECHAMENTO_POR_DRE_SITUACAO = """
select
    trim(replace(d.abreviacao, 'DRE -', '')) as dre,
    case when cfct.status in (0, 1) then 0 else cfct.status end as situacao,
    count(cfct.id) as quantidade
from consolidado_fechamento_componente_turma cfct
inner join turma t on t.id = cfct.turma_id
inner join ue on ue.id = t.ue_id
inner join dre d on d.id = ue.dre_id
where t.tipo_turma in (1, 2, 7)
    and t.ano_letivo = %(ano_letivo)s
    and cfct.bimestre = %(bimestre)s
    and not cfct.excluido
    and (
        (%(segmento)s = 'fundamental_medio' and t.modalidade_codigo in (5, 6))
        or (
            %(segmento)s = 'eja'
            and t.modalidade_codigo = 3
            and t.semestre = %(semestre)s
        )
    )
group by 1, 2
"""

CONSELHO_CLASSE_POR_DRE_SITUACAO = """
select
    trim(replace(d.abreviacao, 'DRE -', '')) as dre,
    cccat.status as situacao,
    count(distinct cccat.aluno_codigo) as quantidade
from consolidado_conselho_classe_aluno_turma cccat
inner join consolidado_conselho_classe_aluno_turma_nota cccatn
    on cccatn.consolidado_conselho_classe_aluno_turma_id = cccat.id
inner join conselho_classe_aluno cca
    on cca.aluno_codigo = cccat.aluno_codigo
inner join conselho_classe cc on cc.id = cca.conselho_classe_id
inner join fechamento_turma ft on ft.id = cc.fechamento_turma_id
inner join turma t on t.id = ft.turma_id and cccat.turma_id = t.id
inner join ue on ue.id = t.ue_id
inner join dre d on d.id = ue.dre_id
where t.tipo_turma = 1
    and t.ano_letivo = %(ano_letivo)s
    and coalesce(cccatn.bimestre, 0) = %(bimestre)s
    and not cccat.excluido
    and (
        (%(segmento)s = 'fundamental_medio' and t.modalidade_codigo in (5, 6))
        or (
            %(segmento)s = 'eja'
            and t.modalidade_codigo = 3
            and t.semestre = %(semestre)s
        )
    )
group by 1, 2
"""

# Esperado do conselho: matrículas por turma que o SGP já consolida do EOL.
CONSELHO_CLASSE_PREVISTO_POR_DRE = """
select
    trim(replace(d.abreviacao, 'DRE -', '')) as dre,
    sum(cmt.quantidade) as previsto
from consolidacao_matricula_turma cmt
inner join turma t on t.id = cmt.turma_id
inner join ue on ue.id = t.ue_id
inner join dre d on d.id = ue.dre_id
where t.tipo_turma = 1
    and t.ano_letivo = %(ano_letivo)s
    and (
        (%(segmento)s = 'fundamental_medio' and t.modalidade_codigo in (5, 6))
        or (
            %(segmento)s = 'eja'
            and t.modalidade_codigo = 3
            and t.semestre = %(semestre)s
        )
    )
group by 1
"""


# Bimestres já iniciados do calendário (modalidade 1 = Fund./Médio, 2 = EJA).
PERIODOS_CALENDARIO = """
select
    tc.ano_letivo,
    tc.modalidade,
    tc.semestre,
    pe.bimestre,
    min(pe.periodo_inicio)::date as inicio,
    max(pe.periodo_fim)::date as fim
from tipo_calendario tc
inner join periodo_escolar pe on pe.tipo_calendario_id = tc.id
where tc.ano_letivo between %(ano_inicial)s and %(ano_final)s
    and not tc.excluido
    and tc.modalidade in (1, 2)
group by 1, 2, 3, 4
having min(pe.periodo_inicio)::date <= current_date
order by 1, 2, 3, 4
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
