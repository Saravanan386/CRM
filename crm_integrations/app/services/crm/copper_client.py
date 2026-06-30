from app.services.crm.base_client import BaseCRMClient


class CopperClient(BaseCRMClient):
    provider = "copper"
    display_name = "Copper CRM"
    api_base_url = "https://api.copper.com"
