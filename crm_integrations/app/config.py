from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


def env_list(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "crm-integrations")
    environment: str = os.getenv("ENVIRONMENT", "local")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./crm_integrations.db")
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    frontend_crm_return_path: str = os.getenv("FRONTEND_CRM_RETURN_PATH", "/presales/data-import")
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    cors_origins: list[str] = None

    salesforce_client_id: str = os.getenv("SALESFORCE_CLIENT_ID", "")
    salesforce_client_secret: str = os.getenv("SALESFORCE_CLIENT_SECRET", "")
    hubspot_client_id: str = os.getenv("HUBSPOT_CLIENT_ID", "")
    hubspot_client_secret: str = os.getenv("HUBSPOT_CLIENT_SECRET", "")
    zoho_client_id: str = os.getenv("ZOHO_CLIENT_ID", "")
    zoho_client_secret: str = os.getenv("ZOHO_CLIENT_SECRET", "")
    zoho_accounts_domain: str = os.getenv("ZOHO_ACCOUNTS_DOMAIN", "accounts.zoho.com")
    microsoft_client_id: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    microsoft_client_secret: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    microsoft_tenant: str = os.getenv("MICROSOFT_TENANT", "common")
    pipedrive_client_id: str = os.getenv("PIPEDRIVE_CLIENT_ID", "")
    pipedrive_client_secret: str = os.getenv("PIPEDRIVE_CLIENT_SECRET", "")
    freshsales_client_id: str = os.getenv("FRESHSALES_CLIENT_ID", "")
    freshsales_client_secret: str = os.getenv("FRESHSALES_CLIENT_SECRET", "")
    freshsales_accounts_domain: str = os.getenv("FRESHSALES_ACCOUNTS_DOMAIN", "")
    copper_client_id: str = os.getenv("COPPER_CLIENT_ID", "")
    copper_client_secret: str = os.getenv("COPPER_CLIENT_SECRET", "")
    keap_client_id: str = os.getenv("KEAP_CLIENT_ID", "")
    keap_client_secret: str = os.getenv("KEAP_CLIENT_SECRET", "")

    def __post_init__(self):
        if self.cors_origins is None:
            object.__setattr__(self, "cors_origins", env_list("CORS_ORIGINS", "http://localhost:3000"))


settings = Settings()
