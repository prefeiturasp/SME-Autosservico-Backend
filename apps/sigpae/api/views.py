"""Views do app sigpae."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sigpae import service
from apps.sigpae.api.serializers import MetricasSigpaeSerializer


class MetricasSigpaeView(APIView):
    """Métricas do SIGPAE para o dashboard, via leitura direta do banco.

    Lê o cache local de métricas já consolidadas. Quando o cache está
    frio, consulta o banco do SIGPAE na hora; em caso de falha, devolve
    o contrato com indicadores nulos.
    """

    serializer_class = MetricasSigpaeSerializer

    @extend_schema(
        tags=["sigpae"],
        summary="Métricas do SIGPAE",
        operation_id="sigpae_metricas",
        responses=MetricasSigpaeSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do SIGPAE.

        Returns:
            Response: contrato de métricas (bloco ``usuarios``).
        """
        serializer = self.serializer_class(data=service.obter_metricas())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
