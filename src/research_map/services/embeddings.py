from collections.abc import Sequence
from dataclasses import dataclass, replace

from research_map.db.repositories import ChunkInput
from research_map.services.ai_provider import AIProvider, AIProviderResponseError


@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    dimensions: int = 1536
    batch_size: int = 64

    def __post_init__(self) -> None:
        if self.dimensions < 1:
            raise ValueError("dimensions must be positive")
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")


class EmbeddingService:
    """Generate and validate embeddings for retrieval-ready chunks."""

    def __init__(
        self,
        provider: AIProvider,
        config: EmbeddingConfig | None = None,
    ) -> None:
        self.provider = provider
        self.config = config or EmbeddingConfig()

    async def embed_chunks(self, chunks: Sequence[ChunkInput]) -> list[ChunkInput]:
        embedded_chunks: list[ChunkInput] = []
        batch_size = self.config.batch_size

        for start in range(0, len(chunks), batch_size):
            batch = list(chunks[start : start + batch_size])
            response = await self.provider.embed([chunk.content for chunk in batch])
            if len(response.vectors) != len(batch):
                raise AIProviderResponseError(
                    "embedding provider returned an unexpected vector count"
                )
            if response.dimensions != self.config.dimensions:
                raise AIProviderResponseError(
                    "embedding dimensions do not match the configured vector store"
                )
            embedded_chunks.extend(
                replace(chunk, embedding=vector)
                for chunk, vector in zip(batch, response.vectors, strict=True)
            )

        return embedded_chunks
