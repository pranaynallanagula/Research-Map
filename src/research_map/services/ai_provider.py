from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class AIProviderError(RuntimeError):
    """Base error for failures raised by a model provider."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when a provider is missing required configuration."""


class AIProviderResponseError(AIProviderError):
    """Raised when a provider returns an unusable response."""


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.2
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt cannot be empty")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")


@dataclass(frozen=True, slots=True)
class GenerationResponse:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("generation response text cannot be empty")
        if not self.model.strip():
            raise ValueError("generation response model cannot be empty")


@dataclass(frozen=True, slots=True)
class EmbeddingResponse:
    vectors: list[list[float]]
    model: str
    dimensions: int

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("embedding response model cannot be empty")
        if self.dimensions < 1:
            raise ValueError("embedding dimensions must be positive")
        if any(len(vector) != self.dimensions for vector in self.vectors):
            raise ValueError("all embedding vectors must have the declared dimensions")


class AIProvider(Protocol):
    """Provider contract used by generation and retrieval services."""

    @property
    def model_name(self) -> str: ...

    async def generate(self, request: GenerationRequest) -> GenerationResponse: ...

    async def embed(self, texts: Sequence[str]) -> EmbeddingResponse: ...
