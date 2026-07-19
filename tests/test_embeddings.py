import asyncio

import pytest

from research_map.db.repositories import ChunkInput
from research_map.services.ai_provider import (
    EmbeddingResponse,
    GenerationRequest,
    GenerationResponse,
)
from research_map.services.embeddings import EmbeddingConfig, EmbeddingService


class FakeEmbeddingProvider:
    model_name = "test-model"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        return GenerationResponse(text=request.prompt, model=self.model_name)

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        return EmbeddingResponse(
            vectors=[[float(index), 1.0] for index, _ in enumerate(texts)],
            model=self.model_name,
            dimensions=2,
        )


def test_embedding_service_batches_and_attaches_vectors() -> None:
    chunks = [
        ChunkInput(ordinal=0, content="first"),
        ChunkInput(ordinal=1, content="second"),
        ChunkInput(ordinal=2, content="third"),
    ]
    service = EmbeddingService(
        FakeEmbeddingProvider(),
        EmbeddingConfig(dimensions=2, batch_size=2),
    )

    embedded = asyncio.run(service.embed_chunks(chunks))

    assert len(embedded) == 3
    assert embedded[0].embedding == [0.0, 1.0]
    assert embedded[2].embedding == [0.0, 1.0]


def test_embedding_service_rejects_dimension_mismatch() -> None:
    service = EmbeddingService(
        FakeEmbeddingProvider(),
        EmbeddingConfig(dimensions=3),
    )

    with pytest.raises(RuntimeError, match="dimensions"):
        asyncio.run(service.embed_chunks([ChunkInput(ordinal=0, content="text")]))
