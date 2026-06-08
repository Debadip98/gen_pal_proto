# GenPal Question Bank Factory — Streamlit Prototype

A lightweight 3-day proof-of-concept Streamlit app for generating, deduplicating, and exporting question banks using the OpenAI API. LangSmith tracing is optional.

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
