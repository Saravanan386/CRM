from fastapi.testclient import TestClient

from app.main import app
from app.routers.crm import CRM_PROVIDER_REGISTRY
from app.routers.crm_auth import build_provider_response
from app.services.crm_registry import get_crm_provider, list_crm_registry


client = TestClient(app)


def test_catalog_has_nine_providers():
    assert len(CRM_PROVIDER_REGISTRY) == 9


def test_catalog_contains_zoho():
    assert any(item.id == "zoho" for item in CRM_PROVIDER_REGISTRY)


def test_registry_is_source_for_catalog():
    assert [item.id for item in CRM_PROVIDER_REGISTRY] == [item.id for item in list_crm_registry()]


def test_auth_provider_response_marks_unconfigured_oauth_provider():
    hubspot = get_crm_provider("hubspot")

    response = build_provider_response(hubspot, connected_providers=set())

    assert response.id == "hubspot"
    assert response.oauth is True
    assert response.enabled is False
    assert response.connected is False
    assert response.status == "not_configured"
    assert response.connect_url == "/api/crm/hubspot/connect"
    assert response.login_url_endpoint == "/api/crm/auth/hubspot/login-url"


def test_auth_provider_response_marks_existing_connection():
    zoho = get_crm_provider("zoho")

    response = build_provider_response(zoho, connected_providers={"zoho"})

    assert response.connected is True
    assert response.status == "connected"


def test_auth_providers_endpoint_returns_discovery_payload():
    response = client.get("/api/crm/auth/providers")

    assert response.status_code == 200
    payload = response.json()
    assert "crms" in payload
    assert len(payload["crms"]) == 9
    assert {"id", "name", "provider", "enabled", "connected", "status", "connect_url"} <= set(payload["crms"][0])
