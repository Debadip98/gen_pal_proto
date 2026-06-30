# GenPal Question Bank Factory

AI-assisted generation, de-duplication, SME review, and GenPal-ready Excel export
of role-based question banks. Built with a **FastAPI** backend and a **static
HTML/CSS/JavaScript** frontend served by **Apache HTTPD**.

> **Note on Streamlit:** Streamlit was used for the early prototype only. The
> current local demo does **not** use Streamlit. The old UI is retained for
> reference as `app_streamlit_legacy.py` / `api_client_streamlit_legacy.py` and
> is excluded from the run instructions below.

## Architecture

```
Browser ──▶ http://localhost:8080/              (static HTML/CSS/JS via Apache)
        └─▶ http://localhost:8080/api/v1/...     ──proxy──▶ http://127.0.0.1:8000/api/v1/...
                                                                (FastAPI / Uvicorn)
```

- **Apache HTTPD** serves the static frontend from `frontend/public/` and
  reverse-proxies `/api/*` to FastAPI. The browser only ever calls Apache, so
  the frontend uses relative API paths and there are no CORS issues.
- **FastAPI** exposes all endpoints under `/api/v1` and handles question
  generation, duplicate detection, the SME review workflow, Excel export, cost
  tracking, and SQLite persistence.

```
genpal_prototype/
  backend/            FastAPI app (api/, core/, db/, schemas/, services/, pipeline/)
  frontend/
    public/           Served by Apache (index.html, css/, js/, js/pages/)
    src/              Original React/TS source (reference only; not in run path)
  deploy/
    apache/           genpal-httpd.conf + README_APACHE_LOCAL.md
    scripts/          run_backend.bat, build_frontend.bat, copy_frontend_to_apache.bat
  app_streamlit_legacy.py        LEGACY (not used)
  api_client_streamlit_legacy.py LEGACY (not used)
```

## Output contract

The exported workbook always has **one sheet named `Sheet1`** with **exactly
these 11 lowercase columns, in this order**:

```
title, ssid, skill, topic, question_type, career_level, complexity, question, answer, options, reference_url
```

No extra, metadata, summary, validation, or hidden sheets/columns.

- **title** — assigned by the app (not the LLM): sequential `1..N` after final merge.
- **ssid** — from the `Skill ID / SSID` input; same value on every row.
- **skill** — exactly the entered Skill Name.
- **topic** — only from the user Topic List, preserved exactly.
- **question_type** — always `QnA`.
- **career_level** — one of `ASE, SE, SSE, TL, AM, M, SM`.
- **complexity** — one of `Basic, Intermediate, Advanced, Proficient, Expert`.
- **question / answer** — scenario-based QnA; no MCQ, no options.
- **options** — always blank.
- **reference_url** — only from the user Reference URL List, unmodified.

Output filename: `<Skill Name>-<SSID>.xlsx`. Review metadata (review status, SME
feedback, LLM suggestions) is shown in the UI only and is **never** exported.

## Prerequisites

- **Python 3.10+**
- **Apache HTTPD 2.4+** (Windows: [Apache Lounge](https://www.apachelounge.com/) or [XAMPP](https://www.apachefriends.org/))
- An **OpenAI API key** — only required when not using mock mode.

## Setup

### 1. Install backend dependencies

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bat
copy .env.example .env
```

Edit `.env`. For a no-cost demo, leave `OPENAI_API_KEY` blank and keep
`USE_MOCK_DATA=true`. Keep `APP_BASE_URL=http://localhost:8080` so SME review
links point at the Apache-hosted frontend.

### 3. Run the FastAPI backend (Terminal 1)

```bat
deploy\scripts\run_backend.bat
```

or manually:

```bat
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Configure Apache HTTPD

1. Enable modules in `httpd.conf`: `mod_proxy`, `mod_proxy_http`, `mod_headers`,
   `mod_rewrite`.
2. In `deploy/apache/genpal-httpd.conf`, set `Define GENPAL_ROOT` to your
   checkout path (forward slashes).
3. Include it from `httpd.conf`:
   `Include "C:/.../Genpal_prototype/deploy/apache/genpal-httpd.conf"`

Full details + troubleshooting: `deploy/apache/README_APACHE_LOCAL.md`.

### 5. Start / restart Apache

- Apache Lounge: `httpd -k restart` (validate first with `httpd -t`)
- XAMPP: Stop, then Start, Apache in the control panel.

### 6. Open the app

- Frontend: <http://localhost:8080>
- Health through Apache: <http://localhost:8080/api/v1/health> → `{"status":"ok",...}`

## Mock mode vs. real API mode

- **Mock mode** (default): `USE_MOCK_DATA=true`, `OPENAI_API_KEY` blank. Runs the
  full UI and workflow with deterministic mock data — no OpenAI billing. The
  header shows a **Mock Mode** badge.
- **Real API mode**: set `OPENAI_API_KEY` and `USE_MOCK_DATA=false`. Generation,
  embeddings, and review suggestions call OpenAI. The header shows **Live API**.

## Using the app

1. **Request Intake** (`#/`) — enter skill, SSID, emails, topics, URLs, career
   levels, and threshold, then **Generate Question Bank**.
2. **Docs Discovery / Generation** — optionally select docs, then watch
   generation progress; you're routed to the dashboard when done.
3. **Requestor Dashboard** (`#/dashboard?job_token=...`) — monitor review
   progress and notifications; download Draft Excel.
4. **Send to SME** — creates a secure review link
   `http://localhost:8080/#/review?review_token=...` and (optionally) emails it.
5. **SME Review** (`#/review?review_token=...`) — accept / reject / regenerate
   each question, compare versions, check doc alignment, then complete the review.
6. **Export / Cost / Business Flow** — download Approved Excel, view cost &
   traceability, and the end-to-end flow.

### Testing the SME review link

After **Send to SME**, copy the displayed link (or read it from the backend
response/email) and open it in a new tab. A `review_token` switches the app into
the SME interface automatically.

### Downloading Excel

- **Draft** — available once rows exist; may include pending questions (UI shows
  a warning; the file itself carries no review metadata).
- **Approved** — enabled once all questions are accepted (no pending, no
  rejected). Both buttons hit `GET /api/v1/jobs/{id}/export?type=draft|approved`
  through Apache and trigger a browser download.

## API reference (under `/api/v1`)

`GET /health` · `POST /jobs` · `GET /jobs/{id}` · `POST /jobs/{id}/generate` ·
`GET /jobs/{id}/questions` · `GET /jobs/{id}/cost-summary` ·
`POST /jobs/{id}/discover-docs` · `POST /jobs/{id}/select-docs` ·
`POST /jobs/{id}/send-sme-review` · `GET /review/{token}` ·
`POST /review/{token}/questions/{qid}/accept|reject|suggestion|regenerate` ·
`POST /review/{token}/versions/{vid}/accept|reject` ·
`GET /dashboard/{job_token}` · `GET /jobs/{id}/export`.

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Frontend can't reach API / network error | FastAPI not running. Start `deploy\scripts\run_backend.bat`. |
| `502 Proxy Error` | Backend down or wrong port. Confirm Uvicorn on `127.0.0.1:8000`. |
| `/api/v1/health` returns Apache 404 | `mod_proxy`/`mod_proxy_http` not enabled, or `ProxyPass` missing. |
| CORS error in console | You bypassed Apache. Always browse via `http://localhost:8080`. |
| `AH00526` duplicate `Listen` | Remove the extra `Listen 8080` from `httpd.conf`. |
| Excel "download" shows JSON/text | The export request didn't reach the proxied backend endpoint. |
| JS changes not reflected | Hard-refresh (Ctrl+F5) to bust the module cache. |

## Security notes

- Never commit `.env`; `.env.example` holds only blank/non-sensitive defaults.
- Rotate any API key pasted into a shared channel, screenshot, or commit.
- No official Accenture logo or proprietary brand assets are bundled; the UI uses
  a brand-safe purple accent (`#A100FF`) and a text "GQ" mark.
- The Apache config uses `ProxyRequests Off` (reverse proxy only; no forward proxy).
