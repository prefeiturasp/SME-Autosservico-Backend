"""Consultas SQL de leitura no banco MariaDB do Rolê Agroecológico.

Queries levantadas e validadas no hom no discovery de contrato do Rolê.
O WordPress guarda tudo em ``posts``/``postmeta`` (EAV), e parte dos campos
(``dados_turmas``, ``dados_educadores``, ``dados_acompanhantes`` e
``ids_up_roteiro``) são arrays serializados do PHP: o SQL traz o valor
bruto e a contagem é feita em ``parser.py``/``mapper.py``.

Por isso são só duas consultas, uma linha por inscrição e uma por UP, e
os indicadores saem do mesmo conjunto de linhas (os totais por DRE fecham
com o total de agendamentos).

O prefixo das tabelas muda por ambiente (``ROLE_AGRO_PREFIXO_TABELAS``).
"""

import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_PREFIXO_VALIDO = re.compile(r"^\w+$", re.ASCII)


def prefixo_tabelas() -> str:
    """Prefixo das tabelas do WordPress, validado antes de entrar no SQL.

    Raises:
        ImproperlyConfigured: Quando o prefixo tem algo além de letras,
            números e ``_``.
    """
    prefixo: str = settings.ROLE_AGRO_PREFIXO_TABELAS
    if not _PREFIXO_VALIDO.match(prefixo):
        raise ImproperlyConfigured(
            "ROLE_AGRO_PREFIXO_TABELAS deve ter só letras, números e '_'."
        )
    return prefixo


_POSTS = f"{prefixo_tabelas()}posts"
_POSTMETA = f"{prefixo_tabelas()}postmeta"


def _meta(alias: str, chave: str, post_id: str = "i.ID") -> str:
    """``left join`` de um campo de ``postmeta``."""
    return (
        f"left join {_POSTMETA} {alias} "
        f"on {alias}.post_id = {post_id} and {alias}.meta_key = '{chave}'"
    )


# Uma linha por agendamento. Oferta de almoço e UPs vêm do roteiro da
# inscrição (``id_roteiro_inscricao``). ``data_reservada_para_o_roteiro``
# mistura ``Ymd`` e ``Y-m-d``: a conversão é feita no parser.
INSCRICOES = f"""
select
    i.ID as id,
    i.post_date as criada_em,
    st.meta_value as status,
    dre.meta_value as dre,
    eol.meta_value as codigo_eol_ue,
    dt.meta_value as data_reservada,
    tur.meta_value as dados_turmas,
    edu.meta_value as dados_educadores,
    aco.meta_value as dados_acompanhantes,
    alm.meta_value as oferta_almoco,
    ups.meta_value as ids_up_roteiro
from {_POSTS} i
{_meta("st", "status_inscricao")}
{_meta("dre", "dre")}
{_meta("eol", "codigo_eol_ue")}
{_meta("dt", "data_reservada_para_o_roteiro")}
{_meta("tur", "dados_turmas")}
{_meta("edu", "dados_educadores")}
{_meta("aco", "dados_acompanhantes")}
{_meta("rot", "id_roteiro_inscricao")}
{_meta("alm", "roteiro_com_oferta_de_almoco", "rot.meta_value")}
{_meta("ups", "ids_up_roteiro", "rot.meta_value")}
where i.post_type = 'post_inscricao'
"""  # noqa: S608

# Uma linha por UP publicada; "preservação" = área de preservação ambiental
# e/ou de manancial (campos ACF ``'0'``/``'1'``).
UNIDADES_PRODUTIVAS = f"""
select
    p.ID as id,
    p.post_title as nome,
    max(case when pm.meta_value = '1' then 1 else 0 end) as preservacao
from {_POSTS} p
left join {_POSTMETA} pm
    on pm.post_id = p.ID
    and pm.meta_key in ('area_preservacao_ambiental', 'area_manancial')
where p.post_type = 'post_up'
    and p.post_status = 'publish'
group by p.ID, p.post_title
"""  # noqa: S608
