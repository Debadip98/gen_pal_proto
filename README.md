# GenPal Question Bank Factory — Streamlit Prototype

A lightweight proof-of-concept Streamlit app for generating, deduplicating, and exporting question banks using the OpenAI API. LangSmith tracing is optional.

## Output contract

The exported workbook always has **one sheet named `Sheet1`** with **exactly these 11 lowercase columns, in this order**:

```
title, ssid, skill, topic, question_type, career_level, complexity, question, answer, options, reference_url
```

No extra, metadata, summary, validation, or hidden sheets/columns. Column rules:

- **title** — assigned by the app (not the LLM): sequential `1..N` after final merge.
- **ssid** — from the `Skill ID / SSID` input; same value on every row.
- **skill** — exactly the entered Skill Name.
- **topic** — only from the user Topic List, preserved exactly.
- **question_type** — always `QnA`.
- **career_level** — one of `ASE, SE, SSE, TL, AM, M, SM`.
- **complexity** — one of `Basic, Intermediate, Advanced, Proficient, Expert`.
- **question / answer** — scenario-based QnA; no MCQ, no options.
- **options** — always blank (empty cell).
- **reference_url** — only from the user Reference URL List, unmodified.

Output filename: `<Skill Name>-<SSID>.xlsx` (e.g. `Microsoft SharePoint Server Development-80002591.xlsx`).

## Inputs and modes

Landing page inputs: **Skill Name**, **Skill ID / SSID**, **Topic List** (one per line), **Reference URL List** (one per line), **Career Level Control**, and **Generation Mode**.

- **Full GenPal Mode** — all 7 career levels, 40 questions each = **280 rows**.
- **Prototype Mode** — selected levels only (default `ASE, SE`), 40 each = `selected × 40` rows.

Generation runs **one career level at a time**, and within a level as five separate LLM calls following the fixed complexity distribution `Basic 5 / Intermediate 6 / Advanced 7 / Proficient 11 / Expert 11` (= 40). One LLM call never spans multiple levels. Each later level receives the questions from already-locked earlier levels as an *Existing Questions to Avoid* list, which reduces cross-level duplicates surfacing in the final check.

## Duplicate checks

Cosine similarity on question embeddings runs twice (threshold `0.85`, configurable via `DUPLICATE_SIMILARITY_THRESHOLD`):

1. **After each career level** — colliding rows are surgically regenerated; if duplicates remain after the retry budget, the level is blocked until regenerated.
2. **Final global repair** across all merged rows — instead of simply blocking, the app automatically repairs duplicates:
   - Duplicate pairs are grouped into **clusters** (connected components). Exact pairs (similarity `1.0`) are reworked without any extra verification.
   - One **canonical** row (the earliest row number) is kept per cluster; the rest are reworked, rewriting **only `question`/`answer`** — every fixed field is preserved.
   - Repair runs in **bounded passes** only (never an unbounded loop) and always ends in one of `FINAL_DUPLICATE_CHECK_PASSED`, `FINAL_MANUAL_REVIEW_REQUIRED`, or `FINAL_REPAIR_FAILED`. Titles are reassigned `1..N` after repair.

Tunables (env-configurable): `MAX_GLOBAL_DUPLICATE_REPAIR_PASSES` (2), `MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW` (2), `MAX_GLOBAL_REWORK_ROWS_PER_PASS` (15), `MIN_IMPROVEMENT_DELTA` (0.01).

Findings and rework details appear in the `Duplicate / Similar Scenario Findings` expander. The download button appears when the final check passes (or after the user confirms a **manual override** for remaining pairs), row validation passes, and the saved workbook is reopened and re-validated against the contract. A manual-override export carries a UI warning and adds **no** extra columns or sheets.

## Local setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the example env file and fill in real values:
   ```bash
   cp .env.example .env
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Mock mode

Leave `OPENAI_API_KEY` blank and set `USE_MOCK_DATA=true` in `.env` to run the UI without calling OpenAI. This is the default when no API key is configured, so you can demo the interface end-to-end without billing.

When `USE_MOCK_DATA=false` and `OPENAI_API_KEY` is missing, the app shows a clear error banner and stops — it will not crash.

## Optional access password

Set `APP_PASSWORD` in `.env` (or Streamlit secrets) to gate the prototype behind a shared password. Leave it blank to disable the gate. This is a lightweight prototype gate, not enterprise authentication.

## LangSmith tracing (optional)

- Set both `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` to enable tracing — the sidebar will show "LangSmith tracing enabled".
- If `LANGSMITH_API_KEY` is missing, the app still runs and the sidebar shows "LangSmith tracing not configured".

## Streamlit Cloud deployment

Add the following to your app's **Secrets** panel in Streamlit Cloud (`Settings → Secrets`). `st.secrets` is read before `.env`, so cloud values win when both are present.

```toml
OPENAI_API_KEY = "your_openai_key"
OPENAI_GENERATION_MODEL = "gpt-4o"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

LANGSMITH_TRACING = "true"
LANGSMITH_API_KEY = "your_langsmith_key"
LANGSMITH_PROJECT = "genpal-prototype"

USE_MOCK_DATA = "false"
DUPLICATE_SIMILARITY_THRESHOLD = "0.85"

APP_PASSWORD = "your_demo_password"
```

## Security notes

- Never commit `.env` or `.streamlit/secrets.toml` — both are git-ignored.
- `.env.example` is safe to commit; it must only contain blank or non-sensitive default values.
- Rotate any API key that has been pasted into a shared channel, screenshot, or commit.
- The app never prints or renders API keys; the sidebar only reports a configured / not-configured status.
