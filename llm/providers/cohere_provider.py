# Cohere LLM provider implementation

# llm/providers/cohere_provider.py

import json
import cohere
from typing import Dict, Any

from core.config import config
from llm.base import BaseLLMProvider


class CohereProvider(BaseLLMProvider):

    def __init__(self, model: str):
        if not config.cohere_api_key:
            raise RuntimeError("COHERE_API_KEY not set")
        self.client = cohere.AsyncClient(api_key=config.cohere_api_key)
        self.model = model.replace("cohere/", "")

    async def chat(self, prompt: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat(
                model=self.model,
                message=prompt,
                response_format={"type": "json_object"},
            )
            if not response.text:
                return {}
            return json.loads(response.text)
        except Exception as e:
            raise RuntimeError(f"Cohere call failed: {e}")