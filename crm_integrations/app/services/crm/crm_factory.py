from app.services.crm.base_client import BaseCRMClient
from app.services.crm.copper_client import CopperClient
from app.services.crm.freshsales_client import FreshsalesClient
from app.services.crm.hubspot_client import HubSpotClient
from app.services.crm.insightly_client import InsightlyClient
from app.services.crm.keap_client import KeapClient
from app.services.crm.microsoft_d365_client import MicrosoftD365Client
from app.services.crm.pipedrive_client import PipedriveClient
from app.services.crm.salesforce_client import SalesforceClient
from app.services.crm.zoho_client import ZohoClient


class CRMFactory:
    clients: dict[str, type[BaseCRMClient]] = {
        "salesforce": SalesforceClient,
        "hubspot": HubSpotClient,
        "zoho": ZohoClient,
        "pipedrive": PipedriveClient,
        "microsoft_d365": MicrosoftD365Client,
        "freshsales": FreshsalesClient,
        "copper": CopperClient,
        "insightly": InsightlyClient,
        "keap": KeapClient,
    }

    @classmethod
    def create(cls, provider: str, access_token: str | None = None, api_key: str | None = None) -> BaseCRMClient:
        client_class = cls.clients.get(provider)
        if not client_class:
            raise ValueError(f"Unsupported CRM provider: {provider}")
        return client_class(access_token=access_token, api_key=api_key)

    @classmethod
    def supported_providers(cls) -> list[str]:
        return list(cls.clients.keys())
