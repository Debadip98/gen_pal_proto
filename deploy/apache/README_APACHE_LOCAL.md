# Local Apache HTTPD Setup — GenPal Prototype

Apache serves the static frontend and reverse-proxies `/api/*` to the FastAPI
backend. The browser only ever talks to Apache on `http://localhost:8080`, so
the frontend uses **relative** API paths (`/api/v1/...`) and there are no CORS
issues.

```
Browser ──▶ http://localhost:8080/            (static HTML/CSS/JS)
        └─▶ http://localhost:8080/api/v1/...   ──proxy──▶ http://127.0.0.1:8000/api/v1/...
                                                              (FastAPI / Uvicorn)
```

## Prerequisites

- **Apache HTTPD 2.4+** — on Windows use [Apache Lounge](https://www.apachelounge.com/)
  or [XAMPP](https://www.apachefriends.org/).
- **Python 3.10+** with project dependencies installed (`pip install -r requirements.txt`).

## 1. Enable required Apache modules

In your main `httpd.conf`, ensure these `LoadModule` lines are **uncommented**:

```apache
LoadModule proxy_module        modules/mod_proxy.so
LoadModule proxy_http_module   modules/mod_proxy_http.so
LoadModule headers_module      modules/mod_headers.so
LoadModule rewrite_module      modules/mod_rewrite.so
```

## 2. Point Apache at this project

Open `genpal-httpd.conf` (in this folder) and replace the placeholder:

```apache
Define GENPAL_ROOT "C:/path/to/genpal_prototype"
```

with the real path to your checkout, **using forward slashes**, e.g.
`C:/Users/you/OneDrive - Accenture/Genpal_prototype`.

Then include it from your main `httpd.conf` (add at the very end):

```apache
Include "C:/Users/you/Genpal_prototype/deploy/apache/genpal-httpd.conf"
```

> **Note on `Listen 8080`** — if your main `httpd.conf` already has a
> `Listen 8080`, remove the duplicate from `genpal-httpd.conf` (Apache errors
> on a duplicate Listen). If Apache already listens on `80`, you can either
> change the VirtualHost to `*:80` or keep `8080`.

## 3. Start the backend

In a terminal (Terminal 1):

```bat
deploy\scripts\run_backend.bat
```

or manually:

```bat
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## 4. Start / restart Apache

- **Apache Lounge:** `httpd -k restart` (or `httpd -k start`)
- **XAMPP:** click *Stop* then *Start* for Apache in the control panel.

Validate the config first with: `httpd -t`

## 5. Open the app

- Frontend:  http://localhost:8080
- Health via proxy:  http://localhost:8080/api/v1/health  → `{"status":"ok",...}`

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `502 Proxy Error` on `/api/...` | FastAPI not running. Start `run_backend.bat`. |
| `/api/v1/health` returns Apache 404 | `ProxyPass` not loaded — check `mod_proxy` / `mod_proxy_http` modules. |
| Frontend loads but API calls fail with CORS | You opened the React/dev server directly instead of going through Apache. Use `http://localhost:8080`. |
| `AH00526` duplicate `Listen` | Remove the extra `Listen 8080` (already in main httpd.conf). |
| Static files 403 Forbidden | `Require all granted` missing, or `GENPAL_ROOT` path wrong. |
| Excel download opens as text | Ensure you hit the backend `/api/v1/jobs/{id}/export` endpoint (proxied), not a static path. |
| Changes to JS not showing | Hard-refresh (Ctrl+F5) — browser cached the old module. |
