import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from research_map.ingestion.extraction import ExtractedPage


@dataclass(frozen=True, slots=True)
class CleanedPage:
    page_number: int
    text: str
    word_count: int
    width: float
    height: float
    rotation: int


def clean_text(text: str) -> str:
    """Normalize common PDF layout artifacts without removing paragraphs."""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(\w)-\n(\w)", r"\1\2", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n[ \t]*\n+", "\n\n", normalized)
    normalized = re.sub(r"(?<!\n)\n(?!\n)", " ", normalized)
    return normalized.strip()


def clean_pages(pages: Sequence[ExtractedPage]) -> list[CleanedPage]:
    """Clean extracted pages while preserving their original page metadata."""

    return [
        CleanedPage(
            page_number=page.page_number,
            text=cleaned_text,
            word_count=len(cleaned_text.split()),
            width=page.width,
            height=page.height,
            rotation=page.rotation,
        )
        for page in pages
        if (cleaned_text := clean_text(page.text))
    ]
