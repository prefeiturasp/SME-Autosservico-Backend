"""Serializers da API do app role_agroecologico."""

from rest_framework import serializers


class RoleItemContagemSerializer(serializers.Serializer):
    """Item de uma tabela por DRE (rótulo + total)."""

    # ``label`` sombreia ``Field.label`` só na tipagem: em runtime o DRF
    # trata campos declarados. O nome vem do contrato com o BFF.
    label = serializers.CharField()  # type: ignore[assignment]
    value = serializers.IntegerField()


class RoleVivenciasComRefeicaoSerializer(serializers.Serializer):
    """Vivências realizadas que incluíram refeição, com o percentual."""

    valor = serializers.IntegerField()
    total_realizadas = serializers.IntegerField()
    progresso_percentual = serializers.FloatField(allow_null=True)


class RoleParticipacaoLogisticaSerializer(serializers.Serializer):
    """Bloco de indicadores de participação e logística."""

    vivencias_realizadas = serializers.IntegerField()
    estudantes_participantes = serializers.IntegerField()
    estudantes_inscritos = serializers.IntegerField()
    participantes_vivencias = serializers.IntegerField()
    educadores_participantes = serializers.IntegerField()
    refeicoes_estudantes = serializers.IntegerField()
    kits_distribuidos = serializers.IntegerField(allow_null=True)
    vivencias_com_refeicao = RoleVivenciasComRefeicaoSerializer()
    ues_participantes_por_dre = RoleItemContagemSerializer(many=True)


class RoleUnidadesProdutivasSerializer(serializers.Serializer):
    """Bloco de unidades produtivas (UPs)."""

    ups_cadastradas = serializers.IntegerField()
    ups_preservacao_ambiental_manancial = serializers.IntegerField()
    ups_que_receberam_visita = serializers.IntegerField()
    lista_ups_que_receberam_visita = serializers.ListField(
        child=serializers.CharField()
    )
    # Sem fonte (a UP é um CNPJ, sem pessoa física): sempre nulo.
    perfil_responsaveis_ups = serializers.DictField(allow_null=True)


class RoleAgendamentosSerializer(serializers.Serializer):
    """Bloco de agendamentos e rolês."""

    agendamentos_totais = serializers.IntegerField()
    agendamentos_ultima_semana = serializers.IntegerField()
    roles_concluidos = serializers.IntegerField()
    roles_previstos_semana = serializers.IntegerField()
    agendamentos_por_dre = RoleItemContagemSerializer(many=True)


class MetricasRoleAgroecologicoSerializer(serializers.Serializer):
    """Contrato de métricas do Rolê Agroecológico entregue ao BFF."""

    atualizado_em = serializers.CharField(allow_null=True)
    indicadores_participacao_logistica = RoleParticipacaoLogisticaSerializer(
        allow_null=True
    )
    unidades_produtivas = RoleUnidadesProdutivasSerializer(allow_null=True)
    agendamentos_roles = RoleAgendamentosSerializer(allow_null=True)
