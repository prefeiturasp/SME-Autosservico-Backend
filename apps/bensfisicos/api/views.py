"""Views do app bensfisicos."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bensfisicos import service
from apps.bensfisicos.api.serializers import MetricasBensFisicosSerializer


class MetricasBensFisicosView(APIView):
    """Métricas do Bens Físicos, lidas do banco do sistema."""

    serializer_class = MetricasBensFisicosSerializer

    @extend_schema(
        tags=["bens-fisicos"],
        summary="Métricas do Bens Físicos",
        operation_id="bens_fisicos_metricas",
        responses=MetricasBensFisicosSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do Bens Físicos."""
        serializer = self.serializer_class(data=service.obter_metricas())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
