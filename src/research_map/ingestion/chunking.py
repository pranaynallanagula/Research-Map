import math
from collections.abc import Sequence
from dataclasses import dataclass

from research_map.db.repositories import ChunkInput
from research_map.ingestion.cleaning import CleanedPage


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    max_words: int = 450
    overlap_words: int = 60

    def __post_init__(self) -> None:
        if self.max_words < 1:
            raise ValueError("max_words must be positive")
        if self.overlap_words < 0:
            raise ValueError("overlap_words cannot be negative")
        if self.overlap_words >= self.max_words:
            raise ValueError("overlap_words must be smaller than max_words")


def estimate_token_count(text: str) -> int:
    """Estimate model tokens using the common four-characters-per-token rule."""

    return max(1, math.ceil(len(text) / 4))


def chunk_pages(
    pages: Sequence[CleanedPage],
    config: ChunkingConfig | None = None,
) -> list[ChunkInput]:
    """Create overlapping, page-aware chunks for semantic retrieval."""

    chunking_config = config or ChunkingConfig()
    chunks: list[ChunkInput] = []
    ordinal = 0

    for page in pages:
        words = page.text.split()
        start = 0
        while start < len(words):
            end = min(start + chunking_config.max_words, len(words))
            content = " ".join(words[start:end])
            chunks.append(
                ChunkInput(
                    ordinal=ordinal,
                    content=content,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    token_count=estimate_token_count(content),
                )
            )
            ordinal += 1
            if end == len(words):
                break
            start = end - chunking_config.overlap_words

    return chunks
