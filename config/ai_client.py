"""
Centralized Gemini client — single source of truth for the model + SDK.

Every other file that talks to Gemini should import from HERE instead of
calling `google.generativeai` / hardcoding model names directly. That way,
the next model bump (3.5 -> 3.6 -> ...) is a one-line change instead of a
13-file hunt.

Uses the new unified `google-genai` SDK (pip install google-genai), not the
old deprecated `google-generativeai` package.
"""
import json
import os
import sys
from functools import lru_cache
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

# ---------------------------------------------------------------------------
# Model tiers. Bump versions HERE ONLY.
# ---------------------------------------------------------------------------
MODEL_FLASH      = "gemini-3.5-flash"        # planning / execution / reasoning
MODEL_FLASH_LITE = "gemini-3.5-flash-lite"   # fast, cheap routing / classification

# Gemini's Live (real-time voice) API is versioned on its own track, separate
# from the main Flash line above — as of this writing the current, non-
# deprecated Live model is 3.1 rather than 3.5. gemini-2.5-flash-native-audio-
# preview-12-2025 (the previous value here) is deprecated; Google's migration
# guidance points to gemini-3.1-flash-live-preview.
MODEL_LIVE       = "gemini-3.1-flash-live-preview"   # Live API: voice loop / screen narration


def _get_api_key() -> str:
    """
    Local/desktop: reads config/api_keys.json.
    Cloud Run: that file doesn't exist in the container (by design - it's
    never baked into the image), so fall back to the GEMINI_API_KEY env var,
    which cloudbuild.yaml injects from Secret Manager
    (--set-secrets=GEMINI_API_KEY=gemini-api-key:latest).
    """
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["gemini_api_key"]
    except FileNotFoundError:
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            return env_key
        raise RuntimeError(
            "No Gemini API key found: config/api_keys.json is missing and "
            "the GEMINI_API_KEY environment variable is not set."
        )


def get_api_key() -> str:
    """Public accessor for the Gemini API key — for callers that need the
    raw key (e.g. to build a Client with non-default http_options) rather
    than the cached client from get_client()."""
    return _get_api_key()


@lru_cache(maxsize=1)
def get_client():
    """Cached google-genai Client (Gemini Developer API)."""
    from google import genai
    return genai.Client(api_key=_get_api_key())


def generate(
    model: str,
    contents,
    system_instruction: str | None = None,
    **config_kwargs,
):
    """
    Drop-in replacement for the old:
        genai.configure(api_key=...)
        model = genai.GenerativeModel(model_name=..., system_instruction=...)
        model.generate_content(contents)

    Usage:
        from config.ai_client import generate, MODEL_FLASH
        response = generate(MODEL_FLASH, "some prompt", system_instruction="...")
        text = response.text
    """
    from google.genai import types

    config = None
    if system_instruction or config_kwargs:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            **config_kwargs,
        )

    client = get_client()
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )