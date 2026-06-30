# CRM Integrations Backend

FastAPI backend for connecting 9 CRM providers to your existing frontend.

## Supported CRMs

- Salesforce
- HubSpot CRM
- Zoho CRM
- Pipedrive
- Microsoft D365
- Freshsales
- Copper CRM
- Insightly CRM
- Keap

## Setup

Set required environment variables:

```powershell
$env:ENCRYPTION_KEY="{strong_random_secret}"
$env:FRONTEND_BASE_URL="http://localhost:3000"
$env:API_BASE_URL="http://localhost:8000"
```

```powershell
cd crm_integrations
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Frontend API Flow

Load available CRM cards:

```http
GET /api/crm/providers
```

Open provider OAuth login page:

```http
GET /api/crm/auth/zoho/connect?workspace_name={workspace_name}&login_email={login_email}&sync_scope=full
```

Alternative if your frontend wants the URL as JSON:

```http
GET /api/crm/auth/zoho/login-url?workspace_name={workspace_name}&login_email={login_email}&sync_scope=full
```

OAuth redirect flow:

```text
Your CRM frontend
  -> user clicks Salesforce / HubSpot / Zoho Connect
  -> frontend opens /api/crm/auth/{provider}/connect
  -> provider login and permission page opens
  -> provider redirects to /api/crm/auth/{provider}/callback?code=...&state=...
  -> backend exchanges code for tokens
  -> backend saves encrypted access/refresh token
  -> backend redirects to FRONTEND_BASE_URL/crm/connections?provider={provider}&status=connected
  -> frontend refreshes GET /api/crm/providers and shows Connected
```

Connect a CRM after your login page submits:

```http
POST /api/crm/connections
Content-Type: application/json
```

```json
{
  "provider": "zoho",
  "workspace_name": "{workspace_name}",
  "login_email": "{login_email}",
  "credential": "{oauth_code_or_api_key}",
  "sync_scope": "full",
  "allow_collab": true,
  "auto_sync": true
}
```

List connected CRMs:

```http
GET /api/crm/connections
```

Disconnect:

```http
DELETE /api/crm/connections/zoho
```

Start sync:

```http
POST /api/crm/sync/zoho
Content-Type: application/json
```

```json
{
  "provider": "zoho",
  "sync_type": "manual",
  "resources": ["contacts", "leads"]
}
```

OAuth login URL:

```http
GET /api/crm/auth/zoho/login-url
```

Webhook receiver:

```http
POST /api/crm/webhooks/zoho
```

## Notes

The provider clients are integration-ready adapters. Add each provider's real API resource endpoints inside `app/services/crm/*_client.py` as credentials become available.

Tokens and API keys are encrypted before storage with `ENCRYPTION_KEY`.
