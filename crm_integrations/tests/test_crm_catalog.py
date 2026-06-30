from app.routers.crm import CRM_PROVIDER_REGISTRY


def test_catalog_has_nine_providers():
    assert len(CRM_PROVIDER_REGISTRY) == 9


def test_catalog_contains_zoho():
    assert any(item.id == "zoho" for item in CRM_PROVIDER_REGISTRY)
