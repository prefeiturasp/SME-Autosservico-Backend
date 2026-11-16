"""Views do app role_agroecologico."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.role_agroecologico import service
from apps.role_agroecologico.api.serializers import (
    MetricasRoleAgroecologicoSerializer,
)


class MetricasRoleAgroecologicoView(APIView):
    """Métricas do Rolê Agroecológico, via leitura direta do banco."""

    serializer_class = MetricasRoleAgroecologicoSerializer

    @extend_schema(
        tags=["role-agroecologico"],
        summary="Métricas do Rolê Agroecológico",
        operation_id="role_agroecologico_metricas",
        responses=MetricasRoleAgroecologicoSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do Rolê Agroecológico."""
        serializer = self.serializer_class(data=service.obter_metricas())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
