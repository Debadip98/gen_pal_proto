# GenPal Question Bank Factory

AI-assisted generation, de-duplication, SME review, and GenPal-ready Excel export
of role-based question banks. Built with a **FastAPI** backend that also serves a
**static HTML/CSS/JavaScript** frontend — the whole app runs from **one URL** for
local demos. No Streamlit, no Apache, no reverse proxy required.

> **Note on Streamlit:** Streamlit was used for the early prototype only and is
> not part of the runtime (archived as `app_streamlit_legacy.py` /
> `api_client_streamlit_legacy.py`).

## Architecture (local demo)

```
Browser ──▶ http://127.0.0.1:8000/            (static HTML/CSS/JS, served by FastAPI)
        └─▶ http://127.0.0.1:8000/api/v1/...   (same FastAPI app — no proxy)
```

- **FastAPI** serves the frontend from `frontend/public/` *and* exposes every API
  under `/api/v1` on the same origin. The frontend calls **relative** `/api/v1`
  paths, so there is no cross-origin or connection-refused class of error.
- Handles question generation (mock or OpenAI), duplicate detection, SME review,
  Excel export, cost tracking, and SQLite persistence.
- **Apache is optional** (`deploy/apache/`) for a proxy-style setup, but the
  local demo does not need it.

```
genpal_prototype/
  backend/            FastAPI app (api/, core/, db/, schemas/, services/, pipeline/)
  frontend/public/    Served by FastAPI (index.html, css/, js/, js/pages/)
  scripts/            run_local.bat, smoke_test.bat
  deploy/apache/      Optional Apache reverse-proxy setup
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
- An **OpenAI API key** — only required when *not* using mock mode.

## Quick start (local demo — one URL)

```bat
:: 1. Create + activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

:: 2. Install dependencies
pip install -r requirements.txt

:: 3. Create your env file (defaults are demo-ready: USE_MOCK_DATA=true)
copy .env.example .env

:: 4. Run the app (serves API + frontend on one port)
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Or just double-click **`scripts\run_local.bat`**.

Then:

- **Open the app:** <http://127.0.0.1:8000>
- **Health check:** <http://127.0.0.1:8000/api/v1/health> → `{"status":"ok","service":"genpal-question-bank-api","mock_mode":true}`
- **API docs:** <http://127.0.0.1:8000/docs>
- **Smoke test:** `scripts\smoke_test.bat`

For the demo, keep `USE_MOCK_DATA=true` and leave `OPENAI_API_KEY` blank — no
billing, no external calls. The app runs even if `.env` is missing (safe
defaults). Apache is **not** required; see `deploy/apache/` only if you want the
optional reverse-proxy setup.

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
| `[WinError 10061] ... actively refused it` | The backend isn't running. Start it (`scripts\run_local.bat`) and browse to `http://127.0.0.1:8000` — the same server serves the page and the API. |
| Header shows **Backend offline** | Same as above — start the server, then refresh. |
| `[Errno 10048] address already in use` / port in use | Another process holds `:8000`. Stop it, or run on another port: `uvicorn backend.main:app --port 8010` (then open that port). |
| `.env` missing | App still runs with safe defaults (mock mode). Copy `.env.example` to `.env` to customize. |
| `OPENAI_API_KEY is missing` error | You set `USE_MOCK_DATA=false` without a key. Set `USE_MOCK_DATA=true` for the demo, or add the key. |
| Excel "download" shows JSON/text | Generation hasn't produced rows yet, or schema validation failed — generate first, then download. |
| Blank page | Hard-refresh (Ctrl+F5); confirm you opened `http://127.0.0.1:8000` (not a `file://` path). |

## Security notes

- Never commit `.env`; `.env.example` holds only blank/non-sensitive defaults.
- Rotate any API key pasted into a shared channel, screenshot, or commit.
- No official Accenture logo or proprietary brand assets are bundled; the UI uses
  a brand-safe purple accent (`#A100FF`) and a text "GQ" mark.
