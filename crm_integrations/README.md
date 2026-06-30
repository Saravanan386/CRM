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
<<<<<<< HEAD
$env:API_AUTH_TOKEN="{backend_swagger_auth_token}"
$env:API_AUTH_USERNAME="{swagger_login_username}"
$env:API_AUTH_PASSWORD="{swagger_login_password}"
$env:FRONTEND_BASE_URL="http://localhost:3000"
$env:API_BASE_URL="http://localhost:8000"
=======
$env:FRONTEND_BASE_URL="https://follei-v3.vercel.app"
$env:FRONTEND_CRM_RETURN_PATH="/presales/data-import"
$env:API_BASE_URL="https://your-crm-backend-domain.com"
$env:CORS_ORIGINS="https://follei-v3.vercel.app"
>>>>>>> 9ce9f4307bcf2ced1a25d8ca89a03fcf8603d937
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

## Swagger Authorization

Open:

```text
http://127.0.0.1:8000/docs
```

Click **Authorize** and paste your `API_AUTH_TOKEN` value.
Swagger sends it as:

```text
Authorization: Bearer {API_AUTH_TOKEN}
```

You can get the bearer token from Swagger:

1. Open `POST /api/auth/login`.
2. Enter `API_AUTH_USERNAME` and `API_AUTH_PASSWORD`.
3. Copy `access_token`.
4. Click **Authorize**.
5. Paste the copied token.

Extra auth endpoints:

- `POST /api/auth/token` - same as login, kept for Swagger token naming.
- `GET /api/auth/me` - checks the current bearer token.
- `POST /api/auth/logout` - tells the client to remove the bearer token.

`/health` and the OAuth provider callback route stay open. CRM API routes require the bearer token.

## Frontend API Flow

Load available CRM cards:

```http
GET /api/crm/providers
```

Open provider OAuth login page:

```http
GET /api/crm/auth/zoho/connect?workspace_name={workspace_name}&login_email={login_email}&sync_scope=full
```

Frontend-friendly alias for a real browser navigation:

```http
GET /api/crm/zoho/connect?workspace_name={workspace_name}&login_email={login_email}&sync_scope=full
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
  -> backend redirects to FRONTEND_BASE_URL + FRONTEND_CRM_RETURN_PATH?provider={provider}&connected={provider}&status=connected
  -> frontend refreshes GET /api/crm/providers and shows Connected
```

The frontend should use `window.location.href` for connect clicks, not `fetch`, because the provider login and callback are browser redirects.

```js
window.location.href = `${API_BASE_URL}/api/crm/${provider}/connect?workspace_name=Follei&login_email=${encodeURIComponent(email)}&sync_scope=full`;
```

## OAuth App Credentials

Register Follei in each CRM provider console and set the matching client credentials in the backend environment.

```powershell
$env:ZOHO_CLIENT_ID="{zoho_client_id}"
$env:ZOHO_CLIENT_SECRET="{zoho_client_secret}"
$env:ZOHO_ACCOUNTS_DOMAIN="accounts.zoho.in"

$env:HUBSPOT_CLIENT_ID="{hubspot_client_id}"
$env:HUBSPOT_CLIENT_SECRET="{hubspot_client_secret}"

$env:SALESFORCE_CLIENT_ID="{salesforce_client_id}"
$env:SALESFORCE_CLIENT_SECRET="{salesforce_client_secret}"

$env:MICROSOFT_CLIENT_ID="{microsoft_client_id}"
$env:MICROSOFT_CLIENT_SECRET="{microsoft_client_secret}"
$env:MICROSOFT_TENANT="common"

$env:PIPEDRIVE_CLIENT_ID="{pipedrive_client_id}"
$env:PIPEDRIVE_CLIENT_SECRET="{pipedrive_client_secret}"

$env:FRESHSALES_CLIENT_ID="{freshsales_client_id}"
$env:FRESHSALES_CLIENT_SECRET="{freshsales_client_secret}"
$env:FRESHSALES_ACCOUNTS_DOMAIN="https://your-freshsales-oauth-domain"

$env:COPPER_CLIENT_ID="{copper_client_id}"
$env:COPPER_CLIENT_SECRET="{copper_client_secret}"

$env:KEAP_CLIENT_ID="{keap_client_id}"
$env:KEAP_CLIENT_SECRET="{keap_client_secret}"
```

Register callback URLs byte-for-byte with each provider:

```text
https://your-crm-backend-domain.com/api/crm/auth/{provider}/callback
```

For Zoho India orgs, keep `ZOHO_ACCOUNTS_DOMAIN=accounts.zoho.in` and register the same backend callback URL in the Zoho API Console.

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
