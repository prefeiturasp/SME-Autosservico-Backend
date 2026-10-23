"""Views do app gipe."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gipe import service
from apps.gipe.api.serializers import GipeFiltrosQuerySerializer
from apps.gipe.api.serializers import MetricasGipeSerializer


class MetricasGipeView(APIView):
    """Métricas do GIPE, lidas dos bancos de ocorrências e de usuários."""

    serializer_class = MetricasGipeSerializer

    @extend_schema(
        tags=["gipe"],
        summary="Métricas do GIPE",
        operation_id="gipe_metricas",
        parameters=[GipeFiltrosQuerySerializer],
        responses=MetricasGipeSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do GIPE para o ano letivo."""
        params = GipeFiltrosQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        serializer = self.serializer_class(
            data=service.obter_metricas(params.validated_data["ano_letivo"])
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
