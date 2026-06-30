"""Health, config-status, and OpenAI test endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core import config

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "genpal-question-bank-api",
        "mock_mode": config.use_mock_data(),
        "langsmith_tracing": config.is_langsmith_tracing_enabled(),
        "email_configured": config.is_email_configured(),
    }


@router.get("/config-status")
def config_status():
    """Safe view of how the backend loaded its config. Never returns the key."""
    return {
        "use_mock_data": config.use_mock_data(),
        "openai_api_key_configured": bool(config.get_openai_api_key()),
        "openai_generation_model": config.get_openai_generation_model(),
        "openai_embedding_model": config.get_openai_embedding_model(),
        "langsmith_tracing": config.is_langsmith_tracing_enabled(),
    }


class TestGenerationRequest(BaseModel):
    skill_name: str = "Oracle"
    topic: str = "Oracle Database"
    career_level: str = "ASE"
    complexity: str = "Basic"


@router.post("/openai/test-generation")
def test_generation(req: TestGenerationRequest):
    """Verify OpenAI connectivity with one tiny call, independent of full generation."""
    if config.use_mock_data():
        return {"status": "ok", "mode": "mock", "message": "Mock mode enabled — no OpenAI call made."}

    api_key = config.get_openai_api_key()
    if not api_key:
        raise HTTPException(
            400,
            "OPENAI_API_KEY is missing. Set USE_MOCK_DATA=true for mock mode or configure OPENAI_API_KEY.",
        )

    model = config.get_openai_generation_model()
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write concise enterprise exam questions. Reply with ONE short scenario-based question only — no preamble, no answer."},
                {"role": "user", "content": (
                    f"Skill: {req.skill_name}\nTopic: {req.topic}\n"
                    f"Career level: {req.career_level}\nComplexity: {req.complexity}\n"
                    "Write one short question."
                )},
            ],
            temperature=0.5,
            max_tokens=120,
        )
        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        return {
            "status": "ok",
            "mode": "real_openai",
            "model": model,
            "sample_question": text,
            "usage": {
                "input_tokens": getattr(usage, "prompt_tokens", None),
                "output_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            } if usage else None,
        }
    except Exception as exc:  # sanitized — never leak key or full stack
        raise HTTPException(502, f"OpenAI generation failed: {type(exc).__name__}: {str(exc)[:200]}")
