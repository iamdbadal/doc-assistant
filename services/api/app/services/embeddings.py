from abc import ABC, abstractmethod
from typing import List

import cohere
from app.settings import settings
from tenacity import retry, stop_after_attempt, wait_exponential


class EmbeddingClient(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Converts a list of text strings into a list of vector arrays."""
        pass


class CohereEmbeddingClient(EmbeddingClient):
    """Cohere implementation of the EmbeddingClient."""

    def __init__(self):
        if not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY is missing from environment variables.")

        # settings.cohere_api_key is a SecretStr, so we use get_secret_value()
        self.client = cohere.Client(api_key=settings.cohere_api_key.get_secret_value())

        # embed-english-v3.0 is Cohere's state-of-the-art model.
        # It outputs vectors with 1024 dimensions.
        self.model = "embed-english-v3.0"

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=15),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _call_cohere_api(self, texts: List[str]) -> List[List[float]]:
        """Wrapped API call with exponential backoff for rate limits."""
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document",  # Required by Cohere v3 for text being stored in a DB
        )
        return response.embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # Cohere API has a maximum limit of 96 texts per request on the free tier.
        # We automatically batch the chunks here to prevent payload size errors.
        batch_size = 90
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._call_cohere_api(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings


# Instantiate a singleton to be used across the app
embedding_client: EmbeddingClient = CohereEmbeddingClient()
