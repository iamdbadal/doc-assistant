import abc
import logging
from typing import AsyncGenerator, List

import cohere
import openai
from app.settings import settings

logger = logging.getLogger(__name__)


# --- 1. Abstract Base Interface ---
class LLMClient(abc.ABC):
    """Abstract interface for LLM providers."""

    @abc.abstractmethod
    async def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate a complete text response."""
        pass

    @abc.abstractmethod
    async def generate_stream(
        self, prompt: str, system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming text response (yields tokens)."""
        yield ""  # <-- Fixes Mypy: forces method to be recognized as an async generator

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass


# --- 2. Cohere Implementation (Primary / Free Tier) ---
class CohereLLMClient(LLMClient):
    def __init__(self):
        self.client = cohere.AsyncClient(settings.cohere_api_key.get_secret_value())
        self.model = "command-r-08-2024"

    @property
    def provider_name(self) -> str:
        return "cohere"

    async def generate(self, prompt: str, system_prompt: str) -> str:
        response = await self.client.chat(
            model=self.model, message=prompt, preamble=system_prompt, temperature=0.0
        )
        return response.text

    async def generate_stream(
        self, prompt: str, system_prompt: str
    ) -> AsyncGenerator[str, None]:
        stream = self.client.chat_stream(
            model=self.model, message=prompt, preamble=system_prompt, temperature=0.0
        )
        async for event in stream:
            if event.event_type == "text-generation":
                yield event.text


# --- 3. OpenAI Implementation (Fallback / Production) ---
class OpenAILLMClient(LLMClient):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key missing")
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value()
        )
        self.model = "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, system_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self, prompt: str, system_prompt: str
    ) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# --- 4. The Orchestrator (Fallback Routing) ---
class LLMOrchestrator:
    """Manages routing between different LLM providers with fallback logic."""

    def __init__(self):
        self.clients: List[LLMClient] = []

        try:
            if settings.cohere_api_key:
                self.clients.append(CohereLLMClient())
        except Exception as e:
            logger.warning(f"Could not initialize Cohere client: {e}")

        try:
            if settings.openai_api_key:
                self.clients.append(OpenAILLMClient())
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI client: {e}")

        if not self.clients:
            raise RuntimeError(
                "No LLM clients could be initialized. Please check API keys."
            )

    async def generate(self, prompt: str, system_prompt: str) -> str:
        last_exception = None

        for client in self.clients:
            try:
                logger.info(f"Attempting generation with {client.provider_name}...")
                return await client.generate(prompt, system_prompt)
            except Exception as e:
                logger.warning(
                    f"{client.provider_name} generation failed: {e}. Falling back..."
                )
                last_exception = e

        raise RuntimeError(f"All LLM providers failed. Last error: {last_exception}")

    async def generate_stream(
        self, prompt: str, system_prompt: str
    ) -> AsyncGenerator[str, None]:
        last_exception = None

        for client in self.clients:
            try:
                logger.info(f"Attempting streaming with {client.provider_name}...")
                generator = client.generate_stream(prompt, system_prompt)

                # Fetch the very first chunk using Python's built-in anext() to test for early API errors
                first_chunk = await anext(generator)

                yield first_chunk
                async for chunk in generator:
                    yield chunk

                return

            except StopAsyncIteration:
                return
            except Exception as e:
                logger.warning(
                    f"{client.provider_name} streaming failed: {e}. Falling back..."
                )
                last_exception = e

        raise RuntimeError(
            f"All LLM providers failed during stream initialization. Last error: {last_exception}"
        )


# Singleton instance to be used across the app
llm_orchestrator = LLMOrchestrator()
