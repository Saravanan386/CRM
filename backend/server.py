from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
import argparse
import json
import os
import urllib.error
import urllib.request


HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "")
HF_DATASET_CONFIG = os.getenv("HF_DATASET_CONFIG", "default")
HF_DATASET_SPLIT = os.getenv("HF_DATASET_SPLIT", "train")
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_DATASET_API_BASE = os.getenv("HF_DATASET_API_BASE", "https://datasets-server.huggingface.co")


def int_query(params, name, default, minimum=0, maximum=1000):
    raw_value = params.get(name, [str(default)])[0]
    try:
        value = int(raw_value)
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def text_query(params, name, default):
    value = params.get(name, [default])[0]
    return value.strip() or default


class HuggingFaceDatasetClient:
    def __init__(self, dataset_repo, config, split, token=None, api_base=HF_DATASET_API_BASE):
        self.dataset_repo = dataset_repo
        self.config = config
        self.split = split
        self.token = token
        self.api_base = api_base.rstrip("/")

    @property
    def is_configured(self):
        return bool(self.dataset_repo)

    def rows(self, *, config=None, split=None, offset=0, length=100):
        return self._get(
            "/rows",
            {
                "dataset": self.dataset_repo,
                "config": config or self.config,
                "split": split or self.split,
                "offset": offset,
                "length": length,
            },
        )

    def splits(self):
        return self._get("/splits", {"dataset": self.dataset_repo})

    def size(self, *, config=None, split=None):
        return self._get(
            "/size",
            {
                "dataset": self.dataset_repo,
                "config": config or self.config,
                "split": split or self.split,
            },
        )

    def _get(self, path, params):
        if not self.is_configured:
            raise RuntimeError("HF_DATASET_REPO is not configured")

        url = f"{self.api_base}{path}?{urlencode(params)}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Hugging Face API error {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Hugging Face API request failed: {exc.reason}") from exc


hf_client = HuggingFaceDatasetClient(
    dataset_repo=HF_DATASET_REPO,
    config=HF_DATASET_CONFIG,
    split=HF_DATASET_SPLIT,
    token=HF_TOKEN,
)


class CRMApiHandler(BaseHTTPRequestHandler):
    server_version = "CRMHuggingFaceBackend/1.0"

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            return self.respond_json(
                {
                    "status": "healthy",
                    "service": "crm-huggingface-backend",
                    "datasetConfigured": hf_client.is_configured,
                    "dataset": hf_client.dataset_repo or None,
                }
            )

        if path == "/api/dataset/status":
            return self.respond_json(
                {
                    "provider": "huggingface",
                    "dataset": hf_client.dataset_repo or None,
                    "config": hf_client.config,
                    "split": hf_client.split,
                    "configured": hf_client.is_configured,
                    "tokenConfigured": bool(hf_client.token),
                }
            )

        if path == "/api/dataset/splits":
            return self.respond_hf(lambda: hf_client.splits())

        if path == "/api/dataset/size":
            config = text_query(params, "config", hf_client.config)
            split = text_query(params, "split", hf_client.split)
            return self.respond_hf(lambda: hf_client.size(config=config, split=split))

        if path in {"/api/dataset/rows", "/api/records", "/api/contacts", "/api/leads"}:
            offset = int_query(params, "offset", 0, minimum=0, maximum=10_000_000)
            limit = int_query(params, "limit", 100, minimum=1, maximum=1000)
            config = text_query(params, "config", hf_client.config)
            split = text_query(params, "split", hf_client.split)
            return self.respond_hf(lambda: self.dataset_rows_response(config=config, split=split, offset=offset, limit=limit))

        if path.startswith("/api/connections") or path.startswith("/api/crms"):
            return self.respond_error(
                501,
                "Local CRM connection storage was removed. Use crm_integrations OAuth endpoints for real CRM connections.",
            )

        return self.respond_error(404, "Route not found.")

    def do_POST(self):
        if self.path.startswith("/api/connections") or self.path.startswith("/api/crms"):
            return self.respond_error(
                501,
                "Local CRM writes were removed. Use crm_integrations OAuth endpoints for real CRM connections.",
            )
        return self.respond_error(404, "Route not found.")

    def do_DELETE(self):
        if self.path.startswith("/api/connections") or self.path.startswith("/api/crms"):
            return self.respond_error(
                501,
                "Local CRM deletes were removed. Use crm_integrations OAuth endpoints for real CRM connections.",
            )
        return self.respond_error(404, "Route not found.")

    def dataset_rows_response(self, *, config, split, offset, limit):
        payload = hf_client.rows(config=config, split=split, offset=offset, length=limit)
        rows = payload.get("rows", [])
        return {
            "source": "huggingface",
            "dataset": hf_client.dataset_repo,
            "config": config,
            "split": split,
            "offset": offset,
            "limit": limit,
            "count": len(rows),
            "rows": rows,
        }

    def respond_hf(self, fetcher):
        try:
            payload = fetcher()
        except RuntimeError as exc:
            if "HF_DATASET_REPO is not configured" in str(exc):
                return self.respond_error(
                    503,
                    "Set HF_DATASET_REPO to a Hugging Face dataset repo, for example owner/dataset-name.",
                )
            return self.respond_error(502, str(exc))
        return self.respond_json(payload)

    def respond_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_error(self, status, message):
        self.respond_json({"message": message}, status=status)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def run(host, port):
    server = ThreadingHTTPServer((host, port), CRMApiHandler)
    print(f"CRM Hugging Face backend running at http://{host}:{port}")
    print("Set HF_DATASET_REPO, HF_DATASET_CONFIG, HF_DATASET_SPLIT, and optional HF_TOKEN before running.")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backend API for CRM records from Hugging Face datasets.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(args.host, args.port)
