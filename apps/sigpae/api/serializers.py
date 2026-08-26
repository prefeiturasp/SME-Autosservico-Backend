"""Serializers da API do app sigpae.

Refletem o contrato de entrega ao BFF definido no Discovery
(AB#154283). Indicadores sem fonte de dado são entregues como ``null``.
"""

from rest_framework import serializers


class ComAcessoAtivoSerializer(serializers.Serializer):
    """Usuários com acesso ativo e novos nos últimos 30 dias."""

    total = serializers.IntegerField()
    ativos_30_dias = serializers.IntegerField()


class PorTipoPerfilSerializer(serializers.Serializer):
    """Total de usuários por visão de perfil."""

    codae = serializers.IntegerField(allow_null=True)
    dre = serializers.IntegerField(allow_null=True)
    ue = serializers.IntegerField(allow_null=True)
    empresa = serializers.IntegerField(allow_null=True)


class UsuariosSerializer(serializers.Serializer):
    """Bloco de métricas de usuários do SIGPAE."""

    com_acesso_ativo = ComAcessoAtivoSerializer(allow_null=True)
    unicos_por_dia = serializers.IntegerField(allow_null=True)
    acessos_hoje = serializers.IntegerField(allow_null=True)
    por_tipo_perfil = PorTipoPerfilSerializer()
    comparativo_acessos = serializers.JSONField(allow_null=True)


class MetricasSigpaeSerializer(serializers.Serializer):
    """Contrato de métricas do SIGPAE entregue ao BFF."""

    atualizado_em = serializers.CharField(allow_null=True)
    usuarios = UsuariosSerializer()
