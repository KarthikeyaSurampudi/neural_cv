# Abstract LLM provider
# llm/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLLMProvider(ABC):

    @abstractmethod
    async def chat(self, prompt: str) -> Dict[str, Any]:
        """Send prompt to model and return parsed JSON response."""
        pass
