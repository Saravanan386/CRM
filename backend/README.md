# CRM Hugging Face Backend

This backend does not create or return local CRM records. It reads rows from a Hugging Face dataset on each request.

Important: Hugging Face datasets are external hosted datasets, not live CRM provider APIs. For true live Salesforce/HubSpot/Zoho data, use the OAuth backend under `crm_integrations/`.

## Configure

Set the dataset repo before starting the server:

```powershell
$env:HF_DATASET_REPO="{owner}/{dataset_name}"
$env:HF_DATASET_CONFIG="default"
$env:HF_DATASET_SPLIT="train"
```

Optional OpenAI key for later AI features:

```powershell
$env:OPENAI_API_KEY="{openai_api_key}"
```

## Run

```powershell
python backend/server.py --port 8000
```

## Endpoints

`GET /health`

Returns backend health and whether a Hugging Face dataset is configured.

`GET /api/dataset/status`

Returns the current Hugging Face dataset configuration.

`GET /api/dataset/splits`

Returns splits available for the configured dataset.

`GET /api/dataset/size?config={config}&split={split}`

Returns size information for the configured dataset.

`GET /api/dataset/rows?offset=0&limit=100`

Returns raw Hugging Face dataset rows.

Aliases for frontend naming:

- `GET /api/records?offset=0&limit=100`
- `GET /api/contacts?offset=0&limit=100`
- `GET /api/leads?offset=0&limit=100`

## Removed

`/api/crms` and `/api/connections` now return `501` in this simple server. Use `crm_integrations/` for real OAuth CRM connection status.
