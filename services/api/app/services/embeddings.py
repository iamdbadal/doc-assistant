from abc import ABC, abstractmethod
from typing import List

import cohere
from app.settings import settings
from tenacity import retry, stop_after_attempt, wait_exponential


class EmbeddingClient(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass


class CohereEmbeddingClient(EmbeddingClient):
    """Cohere implementation of the EmbeddingClient."""

    def __init__(self):
        self.model = "embed-english-v3.0"
        self._client = None  # Start with no client

    @property
    def client(self):
        """Lazy initialization: Only connect to Cohere when we actually need it."""
        if not self._client:
            if not settings.cohere_api_key:
                raise ValueError(
                    "COHERE_API_KEY is missing from environment variables."
                )
            self._client = cohere.Client(
                api_key=settings.cohere_api_key.get_secret_value()
            )
        return self._client

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=15),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _call_cohere_api(self, texts: List[str]) -> List[List[float]]:
        # Notice we use self.client here, which triggers the connection if it hasn't happened yet!
        response = self.client.embed(
            texts=texts, model=self.model, input_type="search_document"
        )
        return response.embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        batch_size = 90
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._call_cohere_api(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings


embedding_client: EmbeddingClient = CohereEmbeddingClient()
