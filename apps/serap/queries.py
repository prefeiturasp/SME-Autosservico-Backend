"""Consultas SQL de leitura no banco do SERAp Estudantes.

Fonte das métricas do painel "Provas": a tabela ``prova_aluno`` (ciclo de
vida da prova por aluno). ``status in (2, 5)`` = finalizada; ``status = 1``
= iniciada e não finalizada. Levantado no discovery AB#154284.
"""

# Agregado sem recorte de período (números globais).
PROVAS_AGREGADO = """
select
    count(*) as total,
    count(*) filter (where status in (2, 5)) as finalizadas,
    count(*) filter (where status = 1) as nao_finalizadas,
    count(*) filter (where criado_em::date = current_date)
        as iniciadas_hoje
from prova_aluno
"""

# Agregado recortado por janela de datas ``[inicio, fim)`` sobre
# ``criado_em``. Parâmetros posicionais: (inicio, fim).
PROVAS_AGREGADO_JANELA = """
select
    count(*) as total,
    count(*) filter (where status in (2, 5)) as finalizadas,
    count(*) filter (where status = 1) as nao_finalizadas,
    count(*) filter (where criado_em::date = current_date)
        as iniciadas_hoje
from prova_aluno
where criado_em >= %s and criado_em < %s
"""
