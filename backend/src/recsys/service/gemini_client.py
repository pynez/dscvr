# src/recsys/service/gemini_client.py
"""
Thin wrapper around google-generativeai for structured JSON generation.
Gemini sometimes wraps output in markdown code fences — we strip those before parsing.
"""
from __future__ import annotations

import json
import logging
import os
import re

log = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        _model = genai.GenerativeModel("gemini-1.5-flash")
        log.info("Gemini model initialised ✓")
    except Exception as exc:
        log.error("Failed to initialise Gemini model: %s", exc)
        raise
    return _model


def _strip_fences(text: str) -> str:
    """Remove ``` / ```json fences that Gemini may wrap output in."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def generate_json(prompt: str) -> dict | list:
    """
    Synchronous call to Gemini — returns parsed JSON.
    Call via asyncio.to_thread() from async endpoints.
    """
    model = _get_model()
    response = model.generate_content(prompt)
    raw = response.text
    cleaned = _strip_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        log.error("Gemini JSON parse failed.\nRaw: %s\nCleaned: %s\nError: %s", raw, cleaned, exc)
        raise ValueError(f"Gemini returned unparseable JSON: {exc}") from exc
