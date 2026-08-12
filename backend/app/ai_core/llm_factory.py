"""LLM provider factory.

Reads LLM_PROVIDER from settings and returns the right client.
Supported values:

  nvidia    → NVIDIA NIM API (Nemotron Ultra, Nemotron Super, Llama, etc.)
              Free API key at: https://build.nvidia.com
              Models: nvidia/llama-3.1-nemotron-ultra-253b-v1
                      nvidia/llama-3.1-nemotron-super-49b-v1
                      meta/llama-3.3-70b-instruct

  groq      → Groq Cloud (free tier, very fast inference)
              Free API key at: https://console.groq.com
              Models: llama-3.3-70b-versatile
                      llama3-groq-70b-8192-tool-use-preview
                      mixtral-8x7b-32768
                      gemma2-9b-it

  gemini    → Google Gemini (user has Pro subscription)
              API key at: https://aistudio.google.com/apikey
              Models: gemini-2.0-flash (default, best tool-calling)
                      gemini-1.5-pro
                      gemini-2.0-flash-thinking-exp

  ollama    → Local Ollama (no API key required, runs on your machine)
              Install: https://ollama.ai
              Models: ollama pull llama3.2
                      ollama pull mistral
                      ollama pull deepseek-r1
                      ollama pull nemotron-mini (NVIDIA's local variant)

  anthropic → Anthropic Claude (original provider, kept as option)
              Models: claude-sonnet-4-6, claude-opus-4-6
"""

from __future__ import annotations

from app.ai_core.providers.anthropic import AnthropicClient
from app.ai_core.providers.base import BaseLLMClient
from app.ai_core.providers.gemini import GeminiClient
from app.ai_core.providers.openai_compat import OpenAICompatClient
from app.core.config import get_settings

# NVIDIA NIM endpoint (OpenAI-compatible)
NVIDIA_NIM_BASE = "https://integrate.api.nvidia.com/v1"

# Groq endpoint (OpenAI-compatible)
GROQ_BASE = "https://api.groq.com/openai/v1"


class LLMNotConfiguredError(Exception):
    """Raised when the required API key / config for the selected provider is absent."""


def get_llm_client() -> BaseLLMClient:
    """Return the configured LLM provider client.

    Called once per request -- cheap because it just reads settings and
    constructs a lightweight client object with no persistent connections.
    """
    settings = get_settings()
    provider = (settings.llm_provider or "").lower().strip()

    # ── NVIDIA NIM ──────────────────────────────────────────────────────────
    if provider == "nvidia":
        if not settings.nvidia_api_key:
            raise LLMNotConfiguredError(
                "NVIDIA NIM selected but NVIDIA_API_KEY is not set. "
                "Get a free key at https://build.nvidia.com"
            )
        return OpenAICompatClient(
            base_url=NVIDIA_NIM_BASE,
            model=settings.nvidia_model,
            api_key=settings.nvidia_api_key,
        )

    # ── Groq ────────────────────────────────────────────────────────────────
    if provider == "groq":
        if not settings.groq_api_key:
            raise LLMNotConfiguredError(
                "Groq selected but GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com"
            )
        return OpenAICompatClient(
            base_url=GROQ_BASE,
            model=settings.groq_model,
            api_key=settings.groq_api_key,
        )

    # ── Gemini ──────────────────────────────────────────────────────────────
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMNotConfiguredError(
                "Gemini selected but GEMINI_API_KEY is not set. "
                "Get your key at https://aistudio.google.com/apikey"
            )
        return GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    # ── Ollama (local) ──────────────────────────────────────────────────────
    if provider == "ollama":
        ollama_base = (settings.ollama_base_url or "http://localhost:11434").rstrip("/")
        return OpenAICompatClient(
            base_url=f"{ollama_base}/v1",
            model=settings.ollama_model,
            api_key=None,  # Ollama needs no key
        )

    # ── Anthropic (fallback / explicit) ─────────────────────────────────────
    if provider in ("anthropic", ""):
        if not settings.anthropic_api_key:
            raise LLMNotConfiguredError(
                "No LLM provider configured. Set LLM_PROVIDER and the matching API key. "
                "Supported: nvidia, groq, gemini, ollama, anthropic"
            )
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    raise LLMNotConfiguredError(
        f"Unknown LLM_PROVIDER '{provider}'. "
        "Supported: nvidia, groq, gemini, ollama, anthropic"
    )
