# OpenRouter LLM provider implementation

import json
from typing import Dict, Any
from openai import AsyncOpenAI

from core.config import config
from llm.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):

    def __init__(self, model: str):
        if not config.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_api_key
        )
        self.model = model

    async def chat(self, prompt: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                return {}
            return json.loads(content)
        except Exception as e:
            # Re-raise as a generic error that the service can catch
            raise RuntimeError(f"OpenRouter call failed: {e}")