"""Testes de resolução de rotas do URLconf raiz do projeto."""

from django.conf import settings
from django.urls import resolve
from django.urls import reverse


class TestUrlsRaiz:
    """Testes cobrindo as rotas registradas em config/urls.py."""

    def test_admin_resolve(self) -> None:
        """A rota do admin está registrada em settings.ADMIN_URL."""
        resolver = resolve(f"/{settings.ADMIN_URL}")

        assert resolver.app_name == "admin"

    def test_health_route_resolve_via_core(self) -> None:
        """A rota de health check do app core está incluída na raiz."""
        assert reverse("core:health") == "/api/v1/health/"

    def test_schema_route_resolve(self) -> None:
        """A rota de schema OpenAPI está registrada."""
        assert reverse("api-schema") == "/api/v1/schema/"

    def test_docs_route_resolve(self) -> None:
        """A rota de documentação Swagger está registrada."""
        assert reverse("api-docs") == "/api/v1/docs/"
