import asyncio

import pytest

from research_map.services.ai_provider import (
    AIProvider,
    EmbeddingResponse,
    GenerationRequest,
    GenerationResponse,
)


class FakeProvider:
    model_name = "test-model"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        return GenerationResponse(text=request.prompt, model=self.model_name)

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        return EmbeddingResponse(
            vectors=[[float(len(texts))] for _ in texts],
            model=self.model_name,
            dimensions=1,
        )


def test_provider_contract_supports_generation_and_embeddings() -> None:
    provider: AIProvider = FakeProvider()

    generation = asyncio.run(provider.generate(GenerationRequest("Summarize")))
    embeddings = asyncio.run(provider.embed(["one", "two"]))

    assert generation.text == "Summarize"
    assert generation.model == "test-model"
    assert len(embeddings.vectors) == 2
    assert embeddings.dimensions == 1


def test_generation_request_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="prompt cannot be empty"):
        GenerationRequest(" ")

    with pytest.raises(ValueError, match="temperature"):
        GenerationRequest("Summarize", temperature=2.1)


def test_embedding_response_rejects_inconsistent_dimensions() -> None:
    with pytest.raises(ValueError, match="declared dimensions"):
        EmbeddingResponse(
            vectors=[[0.1, 0.2]],
            model="test-model",
            dimensions=1,
        )
