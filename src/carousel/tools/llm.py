from typing import Any, List, Dict, Union
from crewai import LLM
import os

class GeminiWithGoogleSearch(LLM):
    """
    Custom Gemini LLM that automatically enables Google Search grounding.
    - Injects the 'googleSearch' tool into every call if not present.
    - Configured via environment variables: MODEL and GEMINI_API_KEY.
    """
    _google_search_tool = {"googleSearch": {}}

    def __init__(self, auto_inject_search: bool = True, **kwargs):
        # Simplified to only use environment variables for configuration.
        model = os.getenv("MODEL")
        api_key = os.getenv("GEMINI_API_KEY")

        if not model:
            raise ValueError("Missing MODEL environment variable. Please set it in your .env file.")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY. Set the env var or pass api_key=...")

        # New feature: Makes the search injection optional.
        self.auto_inject_search = auto_inject_search
        super().__init__(model=model, api_key=api_key, **kwargs)

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: List[Dict] | None = None,
        **kwargs,
    ) -> Union[str, Any]:
        
        # If search injection is disabled, just make the call directly.
        if not self.auto_inject_search:
            return super().call(messages=messages, tools=tools, **kwargs)

        # More efficient and direct way to handle the tool list.
        _tools = list(tools) if tools else []
        if self._google_search_tool not in _tools:
            _tools.insert(0, self._google_search_tool)

        return super().call(messages=messages, tools=_tools, **kwargs)
