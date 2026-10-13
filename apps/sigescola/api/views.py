"""Views do app sigescola."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sigescola import service
from apps.sigescola.api.serializers import MetricasSigEscolaSerializer
from apps.sigescola.api.serializers import SigEscolaFiltrosQuerySerializer


class MetricasSigEscolaView(APIView):
    """Métricas do SIG-Escola para o painel da COPLAN, lidas do banco."""

    serializer_class = MetricasSigEscolaSerializer

    @extend_schema(
        tags=["sigescola"],
        summary="Métricas do SIG-Escola (COPLAN)",
        operation_id="sigescola_metricas",
        parameters=[SigEscolaFiltrosQuerySerializer],
        responses=MetricasSigEscolaSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do SIG-Escola para os filtros."""
        params = SigEscolaFiltrosQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        filtros = params.validated_data
        try:
            contrato = service.obter_metricas(
                periodo=filtros.get("periodo"),
                data_inicio=filtros.get("data_inicio"),
                data_fim=filtros.get("data_fim"),
                dre=filtros.get("dre"),
                ue=filtros.get("ue"),
            )
        except service.PeriodoNaoEncontradoError as erro:
            raise ValidationError(
                {"periodo": ["Período não encontrado."]}
            ) from erro
        serializer = self.serializer_class(data=contrato)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
