# get_provider(model)

# llm/factory.py

from typing import Optional
from core.config import config

from llm.providers.cohere_provider import CohereProvider
from llm.providers.openrouter_provider import OpenRouterProvider


def get_llm_provider(model: Optional[str] = None):

    model = model or config.default_model

    if model.startswith("cohere/"):
        return CohereProvider(model)

    return OpenRouterProvider(model)