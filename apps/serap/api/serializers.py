"""Serializers da API do app serap."""

from rest_framework import serializers


class SerapProvasSerializer(serializers.Serializer):
    """Indicadores do painel de provas do SERAp."""

    total = serializers.IntegerField(allow_null=True)
    iniciadas_hoje = serializers.IntegerField(allow_null=True)
    nao_finalizadas = serializers.IntegerField(allow_null=True)
    finalizadas = serializers.IntegerField(allow_null=True)
    percentual_finalizadas = serializers.FloatField(allow_null=True)


class MetricasProvasSerapSerializer(serializers.Serializer):
    """Contrato de métricas de provas do SERAp entregue ao BFF."""

    atualizado_em = serializers.CharField(allow_null=True)
    ano = serializers.IntegerField()
    bimestre = serializers.IntegerField()
    provas = SerapProvasSerializer(allow_null=True)
