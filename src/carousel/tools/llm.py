from typing import Any, List, Dict, Union
from crewai import LLM
import os

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class GeminiWithGoogleSearch(LLM):
    """
    Custom Gemini LLM using Google AI Studio (NOT Vertex) with Google Search grounding.
    - Injects the 'googleSearch' tool each call
    - Enables LiteLLM's web_search_options so search actually runs
    Requires: os.environ['GEMINI_API_KEY'] or pass api_key=...
    """

    def __init__(self, model: str | None = None, api_key: str | None = None, **kwargs):
        model = model or os.getenv("MODEL", "gemini/gemini-1.5-pro-latest")
        api_key = GEMINI_API_KEY
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY. Set the env var or pass api_key=...")

        super().__init__(model=model, api_key=api_key, **kwargs)

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: List[Dict] | None = None,
        callbacks: List[Any] | None = None,
        available_functions: Dict[str, Any] | None = None,
        **kwargs,
    ) -> Union[str, Any]:
        # Inject Gemini's search tool in camelCase
        _tools: List[Dict] = list(tools) if tools else []
        has_google_search = any(
            isinstance(t, dict) and ("googleSearch" in t or "google_search" in t)
            for t in _tools
        )
        if not has_google_search:
            _tools.insert(0, {"googleSearch": {}})

        return super().call(
            messages=messages,
            tools=_tools,
            callbacks=callbacks,
            available_functions=available_functions,
            **kwargs,
        )
